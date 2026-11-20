from django.db import transaction
from django.utils import timezone

from .models import Incident


@transaction.atomic
def enregistrer_incident(*, type_incident, description, mission=None, mesure=None, robot=None, message_id=None):
    """Enregistre un incident, sans doublon lorsque le robot fournit un message_id."""
    if message_id:
        incident = Incident.objects.filter(message_id=message_id).first()
        if incident:
            return incident, False

    incident = Incident.objects.create(
        type_incident=type_incident,
        description=description,
        mission=mission,
        mesure=mesure,
        robot=robot,
        message_id=message_id,
        date_incident=timezone.now(),
    )
    return incident, True
