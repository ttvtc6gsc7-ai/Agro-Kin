from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from irrigation.services import autoriser_irrigation, marquer_commande_envoyee
from mesures.models import Etalonnage
from mesures.services import recevoir_mesure
from missions.models import Robot
from missions.services import ajouter_etape, creer_mission
from parcelles.models import Culture, Parcelle, Seuil, Zone


class ApiSecurityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.operator = User.objects.create_user(username="operator", password="secret")
        self.operator.groups.add(Group.objects.create(name="Operateur"))
        self.visitor = User.objects.create_user(username="visitor", password="secret")
        self.robot = Robot.objects.create(nom="R1", etat_connexion=Robot.EtatConnexion.CONNECTE)
        self.token = "jeton-secret-du-robot"
        self.robot.set_jeton(self.token); self.robot.save(update_fields=["jeton_hash"])
        self.other_robot = Robot.objects.create(nom="R2")
        self.other_robot.set_jeton("autre-jeton"); self.other_robot.save(update_fields=["jeton_hash"])
        culture = Culture.objects.create(nom="Riz", type_culture="cereale")
        parcelle = Parcelle.objects.create(nom="P1", superficie=1, localisation="Lab")
        self.zone = Zone.objects.create(nom="Z1", parcelle=parcelle, culture=culture)
        self.mission = creer_mission(createur=self.operator, robot=self.robot, date_mission=timezone.now())
        ajouter_etape(mission=self.mission, zone=self.zone, ordre=1)
        Seuil.objects.create(zone=self.zone, valeur_min=30, valeur_max=80, duree_max_arrosage=20)
        Etalonnage.objects.create(robot=self.robot, valeur_min=0, valeur_max=1000)
        self.client = APIClient()

    def robot_headers(self, robot=None, token=None):
        robot = robot or self.robot
        return {"HTTP_X_ROBOT_ID": str(robot.identifiant), "HTTP_X_ROBOT_TOKEN": token or self.token}

    def measurement_payload(self, **extra):
        payload = {"robot": self.robot.pk, "mission": self.mission.pk, "zone": self.zone.pk, "valeur_brute": "100", "date_heure": timezone.now().isoformat(), "message_id": str(uuid4())}
        payload.update(extra)
        return payload

    def test_human_routes_require_authentication(self):
        self.assertEqual(self.client.get("/api/parcelles/").status_code, 403)

    def test_frontend_requires_session_and_sets_csrf_cookie(self):
        anonymous = self.client.get("/")
        self.assertEqual(anonymous.status_code, 302)
        self.assertIn("/connexion/", anonymous.url)
        self.client.login(username="operator", password="secret")
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("csrftoken", page.cookies)
        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["username"], "operator")

    def test_login_page_is_public(self):
        response = self.client.get("/connexion/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)

    def test_auth_me_rejects_anonymous_session(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 403)
        self.assertIn("detail", response.json())

    def test_auth_me_anonymous_request_returns_french_error_detail(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 403)
        detail = response.json().get("detail", "")
        self.assertIn("authentification", detail.lower())

    def test_auth_me_authenticated_request_returns_user_data(self):
        self.client.login(username="operator", password="secret")
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["username"], "operator")
        self.assertIn("Operateur", data["groups"])

    def test_session_remains_valid_across_multiple_requests(self):
        self.client.login(username="operator", password="secret")
        first = self.client.get("/api/auth/me/")
        self.assertEqual(first.status_code, 200)
        second = self.client.get("/")
        self.assertEqual(second.status_code, 200)
        third = self.client.get("/api/auth/me/")
        self.assertEqual(third.status_code, 200)
        self.assertEqual(third.json()["username"], "operator")

    def test_post_request_with_invalid_csrf_is_rejected(self):
        csrf_client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(csrf_client.login(username="operator", password="secret"))
        csrf_client.get("/")
        # Sans jeton CSRF
        no_csrf = csrf_client.post("/deconnexion/")
        self.assertEqual(no_csrf.status_code, 403)
        # Avec un jeton CSRF invalide/corrompu
        bad_csrf = csrf_client.post("/deconnexion/", HTTP_X_CSRFTOKEN="token-invalide-12345")
        self.assertEqual(bad_csrf.status_code, 403)

    def test_post_request_with_valid_csrf_is_accepted(self):
        csrf_client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(csrf_client.login(username="operator", password="secret"))
        page = csrf_client.get("/")
        token = page.cookies["csrftoken"].value
        valid_post = csrf_client.post("/deconnexion/", HTTP_X_CSRFTOKEN=token)
        self.assertIn(valid_post.status_code, (200, 302))

    def test_logout_requires_csrf_then_clears_session(self):
        csrf_client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(csrf_client.login(username="operator", password="secret"))
        page = csrf_client.get("/")
        token = page.cookies["csrftoken"].value
        self.assertEqual(csrf_client.get("/api/auth/me/").status_code, 200)
        self.assertEqual(csrf_client.post("/deconnexion/").status_code, 403)
        self.assertEqual(csrf_client.get("/api/auth/me/").status_code, 200)
        logout = csrf_client.post("/deconnexion/", HTTP_X_CSRFTOKEN=token)
        self.assertIn(logout.status_code, (200, 302))
        self.assertEqual(csrf_client.get("/api/auth/me/").status_code, 403)

    def test_only_operator_can_authorize_irrigation(self):
        _, _, recommendation = recevoir_mesure(robot_id=self.robot.pk, mission_id=self.mission.pk, zone_id=self.zone.pk, valeur_brute=100, date_heure=timezone.now(), message_id=uuid4())
        self.client.force_authenticate(self.visitor)
        self.assertEqual(self.client.post(f"/api/recommandations/{recommendation.pk}/autoriser/", {"duree_max": 10}, format="json").status_code, 403)
        self.client.force_authenticate(self.operator)
        self.assertEqual(self.client.post(f"/api/recommandations/{recommendation.pk}/autoriser/", {"duree_max": 10}, format="json").status_code, 201)

    def test_robot_measure_requires_its_own_valid_token(self):
        self.assertEqual(self.client.post("/api/robot/mesures/", self.measurement_payload(), format="json").status_code, 403)
        self.assertEqual(self.client.post("/api/robot/mesures/", self.measurement_payload(), format="json", **self.robot_headers(token="wrong")).status_code, 403)
        self.assertEqual(self.client.post("/api/robot/mesures/", self.measurement_payload(robot=self.other_robot.pk), format="json", **self.robot_headers()).status_code, 400)

    def test_robot_duplicate_message_is_idempotent_at_api_boundary(self):
        payload = self.measurement_payload()
        first = self.client.post("/api/robot/mesures/", payload, format="json", **self.robot_headers())
        second = self.client.post("/api/robot/mesures/", payload, format="json", **self.robot_headers())
        self.assertEqual(first.status_code, 201); self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["mesure"]["id"], second.data["mesure"]["id"])

    def test_robot_cannot_confirm_other_robot_irrigation(self):
        _, _, recommendation = recevoir_mesure(robot_id=self.robot.pk, mission_id=self.mission.pk, zone_id=self.zone.pk, valeur_brute=100, date_heure=timezone.now(), message_id=uuid4())
        irrigation = autoriser_irrigation(recommandation=recommendation, utilisateur=self.operator, duree_max=10); marquer_commande_envoyee(irrigation=irrigation)
        response = self.client.post(f"/api/robot/irrigations/{irrigation.pk}/resultat/", {"succes": True, "duree_reelle": 5}, format="json", **self.robot_headers(self.other_robot, "autre-jeton"))
        self.assertEqual(response.status_code, 404)

    def test_robot_can_confirm_its_irrigation_with_validated_duration(self):
        _, _, recommendation = recevoir_mesure(robot_id=self.robot.pk, mission_id=self.mission.pk, zone_id=self.zone.pk, valeur_brute=100, date_heure=timezone.now(), message_id=uuid4())
        irrigation = autoriser_irrigation(recommandation=recommendation, utilisateur=self.operator, duree_max=10); marquer_commande_envoyee(irrigation=irrigation)
        response = self.client.post(f"/api/robot/irrigations/{irrigation.pk}/resultat/", {"succes": True, "duree_reelle": 11}, format="json", **self.robot_headers())
        self.assertEqual(response.status_code, 400)

    def test_robot_can_only_read_its_missions_steps_and_sent_commands(self):
        mission_response = self.client.get("/api/robot/missions/", **self.robot_headers())
        steps_response = self.client.get(f"/api/robot/missions/{self.mission.pk}/etapes/", **self.robot_headers())
        self.assertEqual(mission_response.status_code, 200)
        self.assertEqual([m["id"] for m in mission_response.data], [self.mission.pk])
        self.assertEqual(steps_response.status_code, 200)
        self.assertEqual(len(steps_response.data), 1)
        _, _, recommendation = recevoir_mesure(robot_id=self.robot.pk, mission_id=self.mission.pk, zone_id=self.zone.pk, valeur_brute=100, date_heure=timezone.now(), message_id=uuid4())
        irrigation = autoriser_irrigation(recommandation=recommendation, utilisateur=self.operator, duree_max=10)
        marquer_commande_envoyee(irrigation=irrigation)
        command_response = self.client.get("/api/robot/irrigations/", **self.robot_headers())
        self.assertEqual(command_response.status_code, 200)
        self.assertEqual([item["id"] for item in command_response.data], [irrigation.pk])
