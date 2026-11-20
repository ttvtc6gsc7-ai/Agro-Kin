import uuid

from django.db import models


class Incident(models.Model):
    class Statut(models.TextChoices):
        OUVERT = "ouvert", "Ouvert"
        RESOLU = "resolu", "Résolu"

    description = models.TextField()
    date_incident = models.DateTimeField()
    type_incident = models.CharField(max_length=100)
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.OUVERT)
    mission = models.ForeignKey("missions.Mission", null=True, blank=True, on_delete=models.PROTECT, related_name="incidents")
    mesure = models.ForeignKey("mesures.Mesure", null=True, blank=True, on_delete=models.PROTECT, related_name="incidents")
    robot = models.ForeignKey("missions.Robot", null=True, blank=True, on_delete=models.PROTECT, related_name="incidents")
    message_id = models.UUIDField(null=True, blank=True, unique=True)

    class Meta:
        ordering = ["-date_incident"]

    def __str__(self):
        return f"{self.type_incident} - {self.date_incident:%Y-%m-%d %H:%M}"
