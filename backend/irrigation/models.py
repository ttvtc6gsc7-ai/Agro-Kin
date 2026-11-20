import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class RecommandationIrrigation(models.Model):
    mesure_source = models.ForeignKey("mesures.Mesure", on_delete=models.PROTECT, related_name="recommandations_irrigation")
    zone = models.ForeignKey("parcelles.Zone", on_delete=models.PROTECT, related_name="recommandations_irrigation")
    creee_le = models.DateTimeField(auto_now_add=True)
    justification = models.TextField()
    duree_max = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Durée maximale en secondes.")
    autorisee_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="recommandations_autorisees")
    autorisee_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["mesure_source", "zone"], name="une_recommandation_par_mesure_et_zone"),
        ]

    def __str__(self):
        return f"Recommandation {self.pk} - {self.zone}"


class Irrigation(models.Model):
    class Statut(models.TextChoices):
        AUTORISEE = "autorisee", "Autorisée"
        COMMANDE_ENVOYEE = "commande_envoyee", "Commande envoyée"
        EXECUTEE = "executee", "Exécutée"
        ECHEC = "echec", "Échec"
        NON_CONFIRMEE = "non_confirmee", "Non confirmée"

    recommandation = models.ForeignKey(RecommandationIrrigation, on_delete=models.PROTECT, related_name="operations")
    mesure_source = models.ForeignKey("mesures.Mesure", on_delete=models.PROTECT, related_name="irrigations")
    zone = models.ForeignKey("parcelles.Zone", on_delete=models.PROTECT, related_name="irrigations")
    mission = models.ForeignKey("missions.Mission", null=True, blank=True, on_delete=models.PROTECT, related_name="irrigations")
    operation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    date_irrigation = models.DateTimeField(auto_now_add=True)
    duree_max = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Durée maximale en secondes.")
    duree_reelle = models.PositiveIntegerField(null=True, blank=True)
    volume = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    origine = models.CharField(max_length=50, default="recommandation")
    statut = models.CharField(max_length=25, choices=Statut.choices, default=Statut.AUTORISEE)
    delai_confirmation_secondes = models.PositiveIntegerField(default=30)
    justification_operations_multiples = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["mesure_source", "zone"],
                condition=models.Q(statut__in=["autorisee", "commande_envoyee", "non_confirmee"]),
                name="une_operation_non_confirmee_par_mesure_et_zone",
            ),
        ]

    def __str__(self):
        return f"Irrigation {self.operation_id} - {self.zone}"
