from django.core.validators import MinValueValidator
from django.db import models


class Etalonnage(models.Model):
    class Etat(models.TextChoices):
        ACTIF = "actif", "Actif"
        INACTIF = "inactif", "Inactif"

    robot = models.ForeignKey("missions.Robot", on_delete=models.PROTECT, related_name="etalonnages")
    date_etalonnage = models.DateTimeField(auto_now_add=True)
    valeur_min = models.DecimalField(max_digits=8, decimal_places=2)
    valeur_max = models.DecimalField(max_digits=8, decimal_places=2)
    etat = models.CharField(max_length=10, choices=Etat.choices, default=Etat.ACTIF)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(valeur_min__lt=models.F("valeur_max")), name="etalonnage_min_inferieur_max"),
            models.UniqueConstraint(fields=["robot"], condition=models.Q(etat="actif"), name="un_etalonnage_actif_par_robot"),
        ]
        ordering = ["-date_etalonnage"]

    def __str__(self):
        return f"Étalonnage {self.robot} du {self.date_etalonnage:%Y-%m-%d}"


class Mesure(models.Model):
    class Statut(models.TextChoices):
        RECUE = "recue", "Reçue"
        VALIDE = "valide", "Valide"
        INVALIDE = "invalide", "Invalide"

    zone = models.ForeignKey("parcelles.Zone", on_delete=models.PROTECT, related_name="mesures")
    mission = models.ForeignKey("missions.Mission", on_delete=models.PROTECT, related_name="mesures")
    robot = models.ForeignKey("missions.Robot", on_delete=models.PROTECT, related_name="mesures")
    valeur_brute = models.DecimalField(max_digits=8, decimal_places=2)
    humidite = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    date_heure = models.DateTimeField()
    est_valide = models.BooleanField(null=True, default=None)
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.RECUE)
    message_id = models.UUIDField(unique=True)
    motif_invalidation = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date_heure"]

    def __str__(self):
        return f"Mesure {self.pk} - {self.zone}"
