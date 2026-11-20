from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from incidents.services import enregistrer_incident
from missions.models import EtapeMission, Mission, Robot
from parcelles.models import Zone

from .models import Etalonnage, Mesure


class ErreurMesure(ValueError):
    pass


def _normaliser_message_id(message_id):
    try:
        return UUID(str(message_id))
    except (TypeError, ValueError) as exc:
        raise ErreurMesure("message_id doit être un UUID valide.") from exc


def _calculer_humidite(valeur_brute, etalonnage):
    """Convertit linéairement la plage d'étalonnage en pourcentage 0-100.

    Cette règle s'appuie sur valeur_min, valeur_max et calculerPourcentage()
    du diagramme UML. Aucune autre formule de correction n'est supposée.
    """
    valeur_brute = Decimal(str(valeur_brute))
    if not etalonnage.valeur_min <= valeur_brute <= etalonnage.valeur_max:
        raise ErreurMesure("La valeur brute est hors de la plage configurée par l'étalonnage.")
    humidite = (valeur_brute - etalonnage.valeur_min) * Decimal("100") / (etalonnage.valeur_max - etalonnage.valeur_min)
    if not Decimal("0") <= humidite <= Decimal("100"):
        raise ErreurMesure("La valeur corrigée est hors de la plage 0 à 100 %.")
    return humidite.quantize(Decimal("0.01"))


@transaction.atomic
def recevoir_mesure(*, robot_id, mission_id, zone_id, valeur_brute, date_heure, message_id, age_maximum_secondes=None):
    """Enregistre une mesure une fois, la valide et déclenche son analyse d'irrigation."""
    message_id = _normaliser_message_id(message_id)
    mesure_existante = Mesure.objects.filter(message_id=message_id).first()
    if mesure_existante:
        return mesure_existante, False, None

    if not isinstance(date_heure, type(timezone.now())) or timezone.is_naive(date_heure):
        raise ErreurMesure("date_heure doit être une date Django consciente du fuseau horaire.")
    if age_maximum_secondes is not None:
        age = timezone.now() - date_heure
        if age.total_seconds() > age_maximum_secondes:
            raise ErreurMesure("La mesure est trop ancienne selon la durée configurée.")

    try:
        valeur_brute = Decimal(str(valeur_brute))
    except Exception as exc:
        raise ErreurMesure("valeur_brute doit être numérique.") from exc

    try:
        robot = Robot.objects.get(pk=robot_id)
        mission = Mission.objects.get(pk=mission_id)
        zone = Zone.objects.get(pk=zone_id)
    except (Robot.DoesNotExist, Mission.DoesNotExist, Zone.DoesNotExist) as exc:
        enregistrer_incident(
            type_incident="message_incoherent",
            description="Références robot, mission ou zone inconnues dans une mesure reçue.",
            message_id=message_id,
        )
        raise ErreurMesure("Le robot, la mission ou la zone n'existe pas.") from exc

    mesure = Mesure.objects.create(
        robot=robot,
        mission=mission,
        zone=zone,
        valeur_brute=valeur_brute,
        date_heure=date_heure,
        message_id=message_id,
    )

    erreurs = []
    if mission.robot_id != robot.id:
        erreurs.append("Le robot ne correspond pas à la mission.")
    if not EtapeMission.objects.filter(mission=mission, zone=zone).exists():
        erreurs.append("La zone ne fait pas partie des étapes de la mission.")
    etalonnage = Etalonnage.objects.filter(robot=robot, etat=Etalonnage.Etat.ACTIF).first()
    if not etalonnage:
        erreurs.append("Aucun étalonnage actif n'est configuré pour ce robot.")

    humidite = None
    if not erreurs:
        try:
            humidite = _calculer_humidite(valeur_brute, etalonnage)
        except ErreurMesure as exc:
            erreurs.append(str(exc))

    if erreurs:
        mesure.est_valide = False
        mesure.statut = Mesure.Statut.INVALIDE
        mesure.motif_invalidation = " ".join(erreurs)
        mesure.save(update_fields=["est_valide", "statut", "motif_invalidation"])
        enregistrer_incident(
            type_incident="mesure_invalide",
            description=mesure.motif_invalidation,
            mission=mission,
            mesure=mesure,
            robot=robot,
        )
        return mesure, True, None

    mesure.humidite = humidite
    mesure.est_valide = True
    mesure.statut = Mesure.Statut.VALIDE
    mesure.save(update_fields=["humidite", "est_valide", "statut"])

    from irrigation.services import analyser_mesure_pour_irrigation

    recommandation = analyser_mesure_pour_irrigation(mesure=mesure)
    return mesure, True, recommandation
