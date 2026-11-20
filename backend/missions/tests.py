from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from parcelles.models import Culture, Parcelle, Zone

from .models import Mission, Robot
from .services import (
    ErreurMission,
    ajouter_etape,
    creer_mission,
    enregistrer_accuse_reception,
    preparer_envoi_mission,
    signaler_perte_communication,
)


class MissionServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="operateur")
        self.robot = Robot.objects.create(nom="Robot A", etat_connexion=Robot.EtatConnexion.CONNECTE, jeton_hash="hash")
        culture = Culture.objects.create(nom="Maïs", type_culture="céréale")
        parcelle = Parcelle.objects.create(nom="Parcelle A", superficie=1, localisation="Test")
        self.zones = [Zone.objects.create(nom=f"Zone {i}", parcelle=parcelle, culture=culture) for i in range(4)]

    def _mission_avec_etapes(self, nombre=4):
        mission = creer_mission(createur=self.user, robot=self.robot, date_mission=timezone.now())
        for ordre, zone in enumerate(self.zones[:nombre], start=1):
            ajouter_etape(mission=mission, zone=zone, ordre=ordre)
        return mission

    def test_mission_valide_est_envoyee_puis_confirmee(self):
        mission = self._mission_avec_etapes()
        preparer_envoi_mission(mission=mission)
        mission.refresh_from_db()
        self.assertEqual(mission.etat_transmission, Mission.EtatTransmission.ENVOYEE)

        enregistrer_accuse_reception(mission=mission)
        mission.refresh_from_db()
        self.assertEqual(mission.statut, Mission.Statut.EN_COURS)
        self.assertEqual(mission.etat_transmission, Mission.EtatTransmission.ACCUSEE_RECEPTION)

    def test_mission_avec_moins_de_quatre_etapes_est_refusee_au_lancement(self):
        mission = self._mission_avec_etapes(nombre=3)
        with self.assertRaises(ErreurMission):
            preparer_envoi_mission(mission=mission)

    def test_robot_occupe_est_refuse(self):
        premiere = self._mission_avec_etapes()
        preparer_envoi_mission(mission=premiere)
        enregistrer_accuse_reception(mission=premiere)
        seconde = self._mission_avec_etapes()
        with self.assertRaises(ErreurMission):
            preparer_envoi_mission(mission=seconde)

    def test_perte_communication_ne_termine_pas_la_mission(self):
        mission = self._mission_avec_etapes()
        preparer_envoi_mission(mission=mission)
        enregistrer_accuse_reception(mission=mission)
        _, incident, cree = signaler_perte_communication(mission=mission)
        mission.refresh_from_db()
        self.assertTrue(cree)
        self.assertEqual(incident.mission_id, mission.id)
        self.assertEqual(mission.statut, Mission.Statut.EN_COURS)
        self.assertEqual(mission.etat_transmission, Mission.EtatTransmission.NON_CONFIRMEE)
