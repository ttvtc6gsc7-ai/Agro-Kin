from django.test import TestCase
from uuid import uuid4

from .models import Incident
from .services import enregistrer_incident


class IncidentServiceTests(TestCase):
    def test_incident_avec_message_identique_est_idempotent(self):
        message_id = uuid4()
        premier, cree = enregistrer_incident(type_incident="obstacle", description="Obstacle", message_id=message_id)
        second, cree_a_nouveau = enregistrer_incident(type_incident="obstacle", description="Obstacle", message_id=message_id)
        self.assertTrue(cree)
        self.assertFalse(cree_a_nouveau)
        self.assertEqual(premier.pk, second.pk)
        self.assertEqual(Incident.objects.count(), 1)
