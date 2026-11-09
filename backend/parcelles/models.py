from django.core.validators import MinValueValidator
from django.db import models


class Culture(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    type_culture = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


class Parcelle(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    localisation = models.CharField(max_length=255)

    def __str__(self):
        return self.nom


class Zone(models.Model):
    nom = models.CharField(max_length=100)
    parcelle = models.ForeignKey(Parcelle, on_delete=models.PROTECT, related_name="zones")
    culture = models.ForeignKey(Culture, on_delete=models.PROTECT, related_name="zones")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["parcelle", "nom"], name="zone_nom_unique_par_parcelle")]

    def __str__(self):
        return f"{self.parcelle} - {self.nom}"


class Seuil(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT, related_name="seuils")
    valeur_min = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    valeur_max = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    duree_max_arrosage = models.PositiveIntegerField(help_text="Durée maximale en secondes.")
    date_configuration = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(valeur_min__lte=models.F("valeur_max")), name="seuil_min_inferieur_max"),
            models.UniqueConstraint(fields=["zone"], condition=models.Q(actif=True), name="un_seuil_actif_par_zone"),
        ]
        ordering = ["-date_configuration"]

    def __str__(self):
        return f"Seuil {self.zone} ({self.valeur_min}-{self.valeur_max})"
