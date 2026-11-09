from django.contrib.auth import get_user_model
from rest_framework import serializers

from incidents.models import Incident
from irrigation.models import Irrigation, RecommandationIrrigation
from mesures.models import Etalonnage, Mesure
from missions.models import EtapeMission, Mission, Robot
from parcelles.models import Culture, Parcelle, Seuil, Zone


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    class Meta:
        model = get_user_model()
        fields = ("id", "username", "first_name", "last_name", "email", "groups", "is_staff")


class CultureSerializer(serializers.ModelSerializer):
    class Meta: model = Culture; fields = "__all__"
class ParcelleSerializer(serializers.ModelSerializer):
    class Meta: model = Parcelle; fields = "__all__"
class ZoneSerializer(serializers.ModelSerializer):
    class Meta: model = Zone; fields = "__all__"
class SeuilSerializer(serializers.ModelSerializer):
    class Meta: model = Seuil; fields = "__all__"; read_only_fields = ("date_configuration",)

class RobotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Robot
        fields = ("id", "identifiant", "nom", "adresse_ip", "etat_connexion", "derniere_connexion")
        read_only_fields = ("identifiant", "derniere_connexion")

class EtapeMissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtapeMission
        fields = "__all__"
        read_only_fields = ("date_debut", "date_fin", "statut")

class MissionSerializer(serializers.ModelSerializer):
    etapes = EtapeMissionSerializer(many=True, read_only=True)
    class Meta:
        model = Mission
        fields = "__all__"
        read_only_fields = ("createur", "statut", "etat_transmission", "date_debut", "date_fin")

class EtalonnageSerializer(serializers.ModelSerializer):
    class Meta: model = Etalonnage; fields = "__all__"; read_only_fields = ("date_etalonnage",)
class MesureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesure
        fields = "__all__"
        read_only_fields = ("humidite", "est_valide", "statut", "motif_invalidation")


class RobotMesureInputSerializer(serializers.Serializer):
    """Contrat entrant du robot; message_id reste volontairement réutilisable."""
    robot = serializers.PrimaryKeyRelatedField(queryset=Robot.objects.all())
    mission = serializers.PrimaryKeyRelatedField(queryset=Mission.objects.all())
    zone = serializers.PrimaryKeyRelatedField(queryset=Zone.objects.all())
    valeur_brute = serializers.DecimalField(max_digits=8, decimal_places=2)
    date_heure = serializers.DateTimeField()
    message_id = serializers.UUIDField()

class RecommandationSerializer(serializers.ModelSerializer):
    class Meta: model = RecommandationIrrigation; fields = "__all__"; read_only_fields = ("creee_le", "autorisee_par", "autorisee_le", "mesure_source", "zone", "justification", "duree_max")
class IrrigationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Irrigation
        fields = "__all__"
        read_only_fields = ("id", "recommandation", "mesure_source", "zone", "mission", "operation_id", "date_irrigation", "duree_max", "duree_reelle", "volume", "origine", "statut", "delai_confirmation_secondes", "justification_operations_multiples")
class IncidentSerializer(serializers.ModelSerializer):
    class Meta: model = Incident; fields = "__all__"; read_only_fields = ("date_incident", "statut")
