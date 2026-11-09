from django.test import TestCase
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.utils import timezone

from parcelles.models import Culture, Parcelle, Seuil, Zone
from missions.models import Robot
from missions.services import ajouter_etape, creer_mission

from .models import Etalonnage, Mesure
from .services import recevoir_mesure


class MesureServiceTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="operateur")
        self.robot = Robot.objects.create(nom="Robot mesures", etat_connexion=Robot.EtatConnexion.CONNECTE, jeton_hash="hash")
        culture = Culture.objects.create(nom="Haricot", type_culture="légumineuse")
        parcelle = Parcelle.objects.create(nom="Parcelle mesures", superficie=1, localisation="Test")
        self.zone = Zone.objects.create(nom="Zone mesures", parcelle=parcelle, culture=culture)
        self.mission = creer_mission(createur=user, robot=self.robot, date_mission=timezone.now())
        ajouter_etape(mission=self.mission, zone=self.zone, ordre=1)
        Seuil.objects.create(zone=self.zone, valeur_min=30, valeur_max=80, duree_max_arrosage=20)

    def _recevoir(self, valeur, message_id=None):
        return recevoir_mesure(
            robot_id=self.robot.id,
            mission_id=self.mission.id,
            zone_id=self.zone.id,
            valeur_brute=valeur,
            date_heure=timezone.now(),
            message_id=message_id or uuid4(),
        )

    def test_mesure_valide_est_etalonnee(self):
        Etalonnage.objects.create(robot=self.robot, valeur_min=0, valeur_max=1000)
        mesure, creee, recommandation = self._recevoir(500)
        self.assertTrue(creee)
        self.assertTrue(mesure.est_valide)
        self.assertEqual(mesure.humidite, 50)
        self.assertIsNone(recommandation)

    def test_mesure_invalide_est_conservee_et_signalee(self):
        Etalonnage.objects.create(robot=self.robot, valeur_min=0, valeur_max=1000)
        mesure, _, recommandation = self._recevoir(1200)
        self.assertFalse(mesure.est_valide)
        self.assertEqual(mesure.statut, Mesure.Statut.INVALIDE)
        self.assertIsNone(recommandation)
        self.assertTrue(mesure.incidents.filter(type_incident="mesure_invalide").exists())

    def test_message_duplique_ne_cree_pas_deux_mesures(self):
        Etalonnage.objects.create(robot=self.robot, valeur_min=0, valeur_max=1000)
        message_id = uuid4()
        premiere, creee, _ = self._recevoir(500, message_id)
        seconde, creee_a_nouveau, _ = self._recevoir(500, message_id)
        self.assertTrue(creee)
        self.assertFalse(creee_a_nouveau)
        self.assertEqual(premiere.pk, seconde.pk)
        self.assertEqual(Mesure.objects.count(), 1)

    def test_absence_etalonnage_rend_la_mesure_invalide(self):
        mesure, _, _ = self._recevoir(500)
        self.assertFalse(mesure.est_valide)
        self.assertIn("Aucun étalonnage actif", mesure.motif_invalidation)
        self.assertTrue(mesure.incidents.filter(type_incident="mesure_invalide").exists())

    def test_message_duplique_retourne_la_mesure_initiale_meme_si_charge_differe(self):
        Etalonnage.objects.create(robot=self.robot, valeur_min=0, valeur_max=1000)
        message_id = uuid4()
        premiere, _, _ = self._recevoir(500, message_id)
        seconde, creee, recommandation = self._recevoir(900, message_id)
        self.assertEqual(premiere.pk, seconde.pk)
        self.assertFalse(creee)
        self.assertIsNone(recommandation)
        self.assertEqual(Mesure.objects.count(), 1)
