from django.db import IntegrityError, transaction
from django.utils import timezone

from incidents.services import enregistrer_incident
from parcelles.models import Seuil

from .models import Irrigation, RecommandationIrrigation


class ErreurIrrigation(ValueError):
    pass


def _utilisateur_peut_autoriser(utilisateur):
    return utilisateur.is_superuser or utilisateur.groups.filter(name__in=["Administrateur", "Operateur"]).exists()


@transaction.atomic
def analyser_mesure_pour_irrigation(*, mesure):
    if not mesure.est_valide or mesure.humidite is None:
        raise ErreurIrrigation("Une mesure invalide ne peut pas générer de recommandation.")

    seuil = Seuil.objects.filter(zone=mesure.zone, actif=True).first()
    if not seuil:
        enregistrer_incident(
            type_incident="seuil_absent",
            description="Aucun seuil actif n'est configuré pour la zone de la mesure.",
            mission=mesure.mission,
            mesure=mesure,
            robot=mesure.robot,
        )
        return None

    if mesure.humidite >= seuil.valeur_min:
        return None

    recommandation, _ = RecommandationIrrigation.objects.get_or_create(
        mesure_source=mesure,
        zone=mesure.zone,
        defaults={
            "justification": f"Humidité corrigée {mesure.humidite} % inférieure au seuil minimal {seuil.valeur_min} %.",
            "duree_max": seuil.duree_max_arrosage,
        },
    )
    return recommandation


@transaction.atomic
def autoriser_irrigation(*, recommandation, utilisateur, duree_max, justification_operation_supplementaire=""):
    if not _utilisateur_peut_autoriser(utilisateur):
        raise ErreurIrrigation("Seuls les opérateurs et administrateurs peuvent autoriser une irrigation.")

    recommandation = RecommandationIrrigation.objects.select_for_update().select_related("mesure_source", "zone").get(pk=recommandation.pk)
    if not recommandation.mesure_source.est_valide:
        raise ErreurIrrigation("Une mesure invalide ne peut pas autoriser une irrigation.")
    if duree_max <= 0 or duree_max > recommandation.duree_max:
        raise ErreurIrrigation("La durée demandée dépasse la durée maximale recommandée.")
    if recommandation.autorisee_par_id:
        raise ErreurIrrigation("Cette recommandation a déjà été autorisée.")
    if recommandation.operations.exists() and not justification_operation_supplementaire:
        raise ErreurIrrigation("Une opération existe déjà ; une justification est requise pour en créer une autre.")

    recommandation.autorisee_par = utilisateur
    recommandation.autorisee_le = timezone.now()
    recommandation.save(update_fields=["autorisee_par", "autorisee_le"])
    try:
        return Irrigation.objects.create(
            recommandation=recommandation,
            mesure_source=recommandation.mesure_source,
            zone=recommandation.zone,
            mission=recommandation.mesure_source.mission,
            duree_max=duree_max,
            justification_operations_multiples=justification_operation_supplementaire,
        )
    except IntegrityError as exc:
        raise ErreurIrrigation("Une opération d'irrigation non confirmée existe déjà pour cette mesure et cette zone.") from exc


@transaction.atomic
def marquer_commande_envoyee(*, irrigation):
    irrigation = Irrigation.objects.select_for_update().get(pk=irrigation.pk)
    if irrigation.statut != Irrigation.Statut.AUTORISEE:
        raise ErreurIrrigation("Seule une irrigation autorisée peut être envoyée au robot.")
    irrigation.statut = Irrigation.Statut.COMMANDE_ENVOYEE
    irrigation.save(update_fields=["statut"])
    return irrigation


@transaction.atomic
def enregistrer_resultat_irrigation(*, irrigation, succes, duree_reelle=None, volume=None):
    irrigation = Irrigation.objects.select_for_update().get(pk=irrigation.pk)
    if irrigation.statut != Irrigation.Statut.COMMANDE_ENVOYEE:
        raise ErreurIrrigation("Aucune commande d'irrigation en attente de résultat.")
    if succes and (duree_reelle is None or duree_reelle > irrigation.duree_max):
        raise ErreurIrrigation("La durée réelle est absente ou dépasse la durée maximale autorisée.")
    irrigation.statut = Irrigation.Statut.EXECUTEE if succes else Irrigation.Statut.ECHEC
    irrigation.duree_reelle = duree_reelle
    irrigation.volume = volume
    irrigation.save(update_fields=["statut", "duree_reelle", "volume"])
    if not succes:
        enregistrer_incident(
            type_incident="irrigation_echec",
            description="Le robot a signalé l'échec de l'opération d'irrigation.",
            mission=irrigation.mission,
            mesure=irrigation.mesure_source,
        )
    return irrigation


@transaction.atomic
def signaler_irrigation_non_confirmee(*, irrigation):
    irrigation = Irrigation.objects.select_for_update().get(pk=irrigation.pk)
    if irrigation.statut != Irrigation.Statut.COMMANDE_ENVOYEE:
        raise ErreurIrrigation("Seule une commande envoyée peut devenir non confirmée.")
    irrigation.statut = Irrigation.Statut.NON_CONFIRMEE
    irrigation.save(update_fields=["statut"])
    enregistrer_incident(
        type_incident="irrigation_non_confirmee",
        description="Aucun résultat d'irrigation n'a été confirmé dans le délai attendu.",
        mission=irrigation.mission,
        mesure=irrigation.mesure_source,
    )
    return irrigation
