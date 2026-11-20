from django.test import TestCase
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from mesures.models import Etalonnage
from mesures.services import recevoir_mesure
from missions.models import Robot
from missions.services import ajouter_etape, creer_mission
from parcelles.models import Culture, Parcelle, Seuil, Zone

from .models import Irrigation
from .services import (
    ErreurIrrigation,
    autoriser_irrigation,
    enregistrer_resultat_irrigation,
    marquer_commande_envoyee,
    signaler_irrigation_non_confirmee,
)


class IrrigationServiceTests(TestCase):
    def setUp(self):
        self.operateur = get_user_model().objects.create_user(username="operateur")
        self.operateur.groups.add(Group.objects.create(name="Operateur"))
        self.visiteur = get_user_model().objects.create_user(username="visiteur")
        self.robot = Robot.objects.create(nom="Robot irrigation", etat_connexion=Robot.EtatConnexion.CONNECTE, jeton_hash="hash")
        culture = Culture.objects.create(nom="Tomate", type_culture="maraîchère")
        parcelle = Parcelle.objects.create(nom="Parcelle irrigation", superficie=1, localisation="Test")
        self.zone = Zone.objects.create(nom="Zone irrigation", parcelle=parcelle, culture=culture)
        self.mission = creer_mission(createur=self.operateur, robot=self.robot, date_mission=timezone.now())
        ajouter_etape(mission=self.mission, zone=self.zone, ordre=1)
        Seuil.objects.create(zone=self.zone, valeur_min=30, valeur_max=80, duree_max_arrosage=20)
        Etalonnage.objects.create(robot=self.robot, valeur_min=0, valeur_max=1000)

    def _recommandation_pour_humidite_insuffisante(self):
        _, _, recommandation = recevoir_mesure(
            robot_id=self.robot.id,
            mission_id=self.mission.id,
            zone_id=self.zone.id,
            valeur_brute=100,
            date_heure=timezone.now(),
            message_id=uuid4(),
        )
        return recommandation

    def test_humidite_insuffisante_cree_recommandation(self):
        recommandation = self._recommandation_pour_humidite_insuffisante()
        self.assertIsNotNone(recommandation)
        self.assertEqual(recommandation.duree_max, 20)

    def test_autorisation_refusee_sans_role(self):
        recommandation = self._recommandation_pour_humidite_insuffisante()
        with self.assertRaises(ErreurIrrigation):
            autoriser_irrigation(recommandation=recommandation, utilisateur=self.visiteur, duree_max=10)

    def test_duree_excessive_et_operation_en_attente_sont_refusees(self):
        recommandation = self._recommandation_pour_humidite_insuffisante()
        with self.assertRaises(ErreurIrrigation):
            autoriser_irrigation(recommandation=recommandation, utilisateur=self.operateur, duree_max=21)

        irrigation = autoriser_irrigation(recommandation=recommandation, utilisateur=self.operateur, duree_max=20)
        self.assertEqual(irrigation.statut, Irrigation.Statut.AUTORISEE)
        with self.assertRaises(ErreurIrrigation):
            autoriser_irrigation(recommandation=recommandation, utilisateur=self.operateur, duree_max=20)

    def test_perte_communication_marque_operation_non_confirmee(self):
        recommandation = self._recommandation_pour_humidite_insuffisante()
        irrigation = autoriser_irrigation(recommandation=recommandation, utilisateur=self.operateur, duree_max=10)
        marquer_commande_envoyee(irrigation=irrigation)
        signaler_irrigation_non_confirmee(irrigation=irrigation)
        irrigation.refresh_from_db()
        self.assertEqual(irrigation.statut, Irrigation.Statut.NON_CONFIRMEE)
        self.assertTrue(irrigation.mesure_source.incidents.filter(type_incident="irrigation_non_confirmee").exists())

    def test_operateur_autorise_et_resultat_trop_long_est_refuse(self):
        recommandation = self._recommandation_pour_humidite_insuffisante()
        irrigation = autoriser_irrigation(recommandation=recommandation, utilisateur=self.operateur, duree_max=10)
        self.assertEqual(recommandation.operations.count(), 1)
        marquer_commande_envoyee(irrigation=irrigation)
        with self.assertRaises(ErreurIrrigation):
            enregistrer_resultat_irrigation(irrigation=irrigation, succes=True, duree_reelle=11)

    def test_duree_maximale_exacte_est_acceptee(self):
        recommandation = self._recommandation_pour_humidite_insuffisante()
        irrigation = autoriser_irrigation(recommandation=recommandation, utilisateur=self.operateur, duree_max=20)
        marquer_commande_envoyee(irrigation=irrigation)
        resultat = enregistrer_resultat_irrigation(irrigation=irrigation, succes=True, duree_reelle=20)
        self.assertEqual(resultat.statut, Irrigation.Statut.EXECUTEE)

    def test_irrigation_non_confirmee_exige_une_commande_envoyee(self):
        recommandation = self._recommandation_pour_humidite_insuffisante()
        irrigation = autoriser_irrigation(recommandation=recommandation, utilisateur=self.operateur, duree_max=10)
        with self.assertRaises(ErreurIrrigation):
            signaler_irrigation_non_confirmee(irrigation=irrigation)
