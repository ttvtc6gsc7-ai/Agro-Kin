from django.db import transaction
from django.utils import timezone

from incidents.services import enregistrer_incident
from parcelles.models import Zone

from .models import EtapeMission, Mission, Robot


class ErreurMission(ValueError):
    pass


@transaction.atomic
def creer_mission(*, createur, robot, date_mission, description=""):
    return Mission.objects.create(createur=createur, robot=robot, date_mission=date_mission, description=description)


@transaction.atomic
def ajouter_etape(*, mission, zone, ordre, description=""):
    if mission.statut != Mission.Statut.PLANIFIEE:
        raise ErreurMission("Les étapes ne peuvent être modifiées que sur une mission planifiée.")
    if not Zone.objects.filter(pk=zone.pk).exists():
        raise ErreurMission("La zone demandée n'existe pas.")
    return EtapeMission.objects.create(mission=mission, zone=zone, ordre=ordre, description=description)


@transaction.atomic
def preparer_envoi_mission(*, mission):
    mission = Mission.objects.select_for_update().select_related("robot").get(pk=mission.pk)
    if mission.statut != Mission.Statut.PLANIFIEE:
        raise ErreurMission("Seule une mission planifiée peut être envoyée.")
    if mission.etapes.count() < 4:
        raise ErreurMission("Une mission doit comporter au moins quatre étapes avant son lancement.")
    if mission.robot.etat_connexion != Robot.EtatConnexion.CONNECTE:
        raise ErreurMission("Le robot n'est pas disponible.")
    if Mission.objects.filter(robot=mission.robot, statut=Mission.Statut.EN_COURS).exclude(pk=mission.pk).exists():
        raise ErreurMission("Ce robot exécute déjà une mission active.")

    mission.etat_transmission = Mission.EtatTransmission.ENVOYEE
    mission.save(update_fields=["etat_transmission"])
    return mission


@transaction.atomic
def enregistrer_accuse_reception(*, mission):
    mission = Mission.objects.select_for_update().get(pk=mission.pk)
    if mission.etat_transmission != Mission.EtatTransmission.ENVOYEE:
        raise ErreurMission("Aucun envoi de mission en attente d'accusé de réception.")
    mission.etat_transmission = Mission.EtatTransmission.ACCUSEE_RECEPTION
    mission.statut = Mission.Statut.EN_COURS
    mission.date_debut = timezone.now()
    mission.save(update_fields=["etat_transmission", "statut", "date_debut"])
    return mission


@transaction.atomic
def interrompre_pour_obstacle(*, mission, description, message_id=None):
    mission = Mission.objects.select_for_update().select_related("robot").get(pk=mission.pk)
    incident, cree = enregistrer_incident(
        type_incident="obstacle",
        description=description,
        mission=mission,
        robot=mission.robot,
        message_id=message_id,
    )
    if cree and mission.statut == Mission.Statut.EN_COURS:
        mission.statut = Mission.Statut.INTERROMPUE
        mission.save(update_fields=["statut"])
    return mission, incident, cree


@transaction.atomic
def terminer_mission(*, mission):
    mission = Mission.objects.select_for_update().get(pk=mission.pk)
    if mission.statut != Mission.Statut.EN_COURS:
        raise ErreurMission("Seule une mission en cours peut être terminée.")
    mission.statut = Mission.Statut.TERMINEE
    mission.date_fin = timezone.now()
    mission.save(update_fields=["statut", "date_fin"])
    return mission


@transaction.atomic
def signaler_perte_communication(*, mission, description="Communication interrompue.", message_id=None):
    mission = Mission.objects.select_for_update().select_related("robot").get(pk=mission.pk)
    mission.etat_transmission = Mission.EtatTransmission.NON_CONFIRMEE
    mission.save(update_fields=["etat_transmission"])
    incident, cree = enregistrer_incident(
        type_incident="communication",
        description=description,
        mission=mission,
        robot=mission.robot,
        message_id=message_id,
    )
    return mission, incident, cree
