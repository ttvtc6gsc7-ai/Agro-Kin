import uuid

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class Robot(models.Model):
    class EtatConnexion(models.TextChoices):
        INCONNU = "inconnu", "Inconnu"
        CONNECTE = "connecte", "Connecté"
        DECONNECTE = "deconnecte", "Déconnecté"

    identifiant = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nom = models.CharField(max_length=100, unique=True)
    adresse_ip = models.GenericIPAddressField(protocol="IPv4", null=True, blank=True)
    etat_connexion = models.CharField(max_length=20, choices=EtatConnexion.choices, default=EtatConnexion.INCONNU)
    derniere_connexion = models.DateTimeField(null=True, blank=True)
    jeton_hash = models.CharField(max_length=128, editable=False)

    def set_jeton(self, jeton):
        self.jeton_hash = make_password(jeton)

    def verifier_jeton(self, jeton):
        return check_password(jeton, self.jeton_hash)

    def __str__(self):
        return self.nom


class Mission(models.Model):
    class Statut(models.TextChoices):
        PLANIFIEE = "planifiee", "Planifiée"
        EN_COURS = "en_cours", "En cours"
        INTERROMPUE = "interrompue", "Interrompue"
        TERMINEE = "terminee", "Terminée"
        ANNULEE = "annulee", "Annulée"

    class EtatTransmission(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        ENVOYEE = "envoyee", "Envoyée"
        ACCUSEE_RECEPTION = "accusee_reception", "Accusée réception"
        NON_CONFIRMEE = "non_confirmee", "Non confirmée"
        ECHEC = "echec", "Échec"

    createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="missions_creees")
    robot = models.ForeignKey(Robot, on_delete=models.PROTECT, related_name="missions")
    date_mission = models.DateTimeField()
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PLANIFIEE)
    etat_transmission = models.CharField(max_length=20, choices=EtatTransmission.choices, default=EtatTransmission.EN_ATTENTE)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Mission {self.pk} - {self.robot}"


class EtapeMission(models.Model):
    class Statut(models.TextChoices):
        PLANIFIEE = "planifiee", "Planifiée"
        EN_COURS = "en_cours", "En cours"
        TERMINEE = "terminee", "Terminée"
        IGNOREE = "ignoree", "Ignorée"

    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="etapes")
    zone = models.ForeignKey("parcelles.Zone", on_delete=models.PROTECT, related_name="etapes_mission")
    ordre = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PLANIFIEE)

    class Meta:
        ordering = ["ordre"]
        constraints = [models.UniqueConstraint(fields=["mission", "ordre"], name="ordre_etape_unique_par_mission")]

    def __str__(self):
        return f"Mission {self.mission_id} - étape {self.ordre}"
