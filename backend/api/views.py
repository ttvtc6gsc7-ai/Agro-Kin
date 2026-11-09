from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from incidents.models import Incident
from incidents.services import enregistrer_incident
from irrigation.models import Irrigation, RecommandationIrrigation
from irrigation.services import ErreurIrrigation, autoriser_irrigation, enregistrer_resultat_irrigation, marquer_commande_envoyee
from mesures.models import Etalonnage, Mesure
from mesures.services import ErreurMesure, recevoir_mesure
from missions.models import EtapeMission, Mission, Robot
from missions.services import ErreurMission, ajouter_etape, creer_mission, enregistrer_accuse_reception, preparer_envoi_mission
from parcelles.models import Culture, Parcelle, Seuil, Zone

from .authentication import RobotTokenAuthentication
from .permissions import IsAdminRole, IsHumanAuthenticated, IsOperatorOrAdmin, IsRobotAuthenticated
from .serializers import *


class HumanModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOperatorOrAdmin]

class CultureViewSet(HumanModelViewSet): queryset = Culture.objects.all(); serializer_class = CultureSerializer
class ParcelleViewSet(HumanModelViewSet): queryset = Parcelle.objects.all(); serializer_class = ParcelleSerializer
class ZoneViewSet(HumanModelViewSet): queryset = Zone.objects.select_related("parcelle", "culture"); serializer_class = ZoneSerializer
class SeuilViewSet(HumanModelViewSet): queryset = Seuil.objects.select_related("zone"); serializer_class = SeuilSerializer
class RobotViewSet(HumanModelViewSet): queryset = Robot.objects.all(); serializer_class = RobotSerializer; permission_classes = [IsAdminRole]
class EtalonnageViewSet(HumanModelViewSet): queryset = Etalonnage.objects.select_related("robot"); serializer_class = EtalonnageSerializer
class IncidentViewSet(HumanModelViewSet):
    queryset = Incident.objects.select_related("mission", "mesure", "robot")
    serializer_class = IncidentSerializer
    http_method_names = ["get", "head", "options"]

class MissionViewSet(HumanModelViewSet):
    queryset = Mission.objects.select_related("robot", "createur").prefetch_related("etapes")
    serializer_class = MissionSerializer
    def perform_create(self, serializer):
        serializer.instance = creer_mission(createur=self.request.user, robot=serializer.validated_data["robot"], date_mission=serializer.validated_data["date_mission"], description=serializer.validated_data.get("description", ""))
    @action(detail=True, methods=["post"])
    def envoyer(self, request, pk=None):
        try: return Response(MissionSerializer(preparer_envoi_mission(mission=self.get_object())).data)
        except ErreurMission as exc: raise ValidationError({"detail": str(exc)})

class EtapeMissionViewSet(HumanModelViewSet):
    queryset = EtapeMission.objects.select_related("mission", "zone")
    serializer_class = EtapeMissionSerializer
    def perform_create(self, serializer):
        serializer.instance = ajouter_etape(mission=serializer.validated_data["mission"], zone=serializer.validated_data["zone"], ordre=serializer.validated_data["ordre"], description=serializer.validated_data.get("description", ""))

class RecommandationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOperatorOrAdmin]
    queryset = RecommandationIrrigation.objects.select_related("mesure_source", "zone", "autorisee_par")
    serializer_class = RecommandationSerializer
    @action(detail=True, methods=["post"])
    def autoriser(self, request, pk=None):
        try:
            irrigation = autoriser_irrigation(recommandation=self.get_object(), utilisateur=request.user, duree_max=request.data.get("duree_max"), justification_operation_supplementaire=request.data.get("justification_operation_supplementaire", ""))
        except (ErreurIrrigation, TypeError, ValueError) as exc: raise ValidationError({"detail": str(exc)})
        return Response(IrrigationSerializer(irrigation).data, status=status.HTTP_201_CREATED)

class IrrigationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOperatorOrAdmin]
    queryset = Irrigation.objects.select_related("recommandation", "mesure_source", "zone", "mission")
    serializer_class = IrrigationSerializer
    @action(detail=True, methods=["post"])
    def envoyer(self, request, pk=None):
        try: return Response(IrrigationSerializer(marquer_commande_envoyee(irrigation=self.get_object())).data)
        except ErreurIrrigation as exc: raise ValidationError({"detail": str(exc)})

@api_view(["GET"])
@permission_classes([IsHumanAuthenticated])
def me(request): return Response(UserSerializer(request.user).data)

@api_view(["GET"])
@permission_classes([IsAdminRole])
def users(request): return Response(UserSerializer(get_user_model().objects.all(), many=True).data)

@api_view(["GET"])
@permission_classes([IsHumanAuthenticated])
def dashboard(request):
    return Response({"missions_par_statut": list(Mission.objects.values("statut").annotate(total=Count("id"))), "incidents_ouverts": Incident.objects.filter(statut="ouvert").count(), "irrigations_non_confirmees": Irrigation.objects.filter(statut="non_confirmee").count()})


@api_view(["GET"])
@permission_classes([IsHumanAuthenticated])
def rapport(request):
    """Rapport synthétique réutilisant les mêmes agrégats que le tableau de bord."""
    return dashboard(request)

@api_view(["POST"])
@authentication_classes([RobotTokenAuthentication])
@permission_classes([IsRobotAuthenticated])
def robot_mesures(request):
    data = RobotMesureInputSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    values = data.validated_data
    if values["robot"].pk != request.user.robot.pk:
        raise ValidationError({"robot": "Un robot ne peut envoyer que ses propres mesures."})
    if values["mission"].robot_id != request.user.robot.pk:
        raise ValidationError({"mission": "Cette mission n'appartient pas au robot authentifié."})
    try: mesure, created, recommandation = recevoir_mesure(robot_id=request.user.robot.pk, mission_id=values["mission"].pk, zone_id=values["zone"].pk, valeur_brute=values["valeur_brute"], date_heure=values["date_heure"], message_id=values["message_id"])
    except ErreurMesure as exc: raise ValidationError({"detail": str(exc)})
    return Response({"mesure": MesureSerializer(mesure).data, "recommandation_id": getattr(recommandation, "pk", None)}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([RobotTokenAuthentication])
@permission_classes([IsRobotAuthenticated])
def robot_missions(request):
    """File de missions du robot authentifié, avec leurs étapes ordonnées."""
    missions = Mission.objects.filter(robot=request.user.robot).prefetch_related("etapes__zone")
    return Response(MissionSerializer(missions, many=True).data)


@api_view(["GET"])
@authentication_classes([RobotTokenAuthentication])
@permission_classes([IsRobotAuthenticated])
def robot_etapes_mission(request, mission_id):
    try:
        mission = Mission.objects.get(pk=mission_id, robot=request.user.robot)
    except Mission.DoesNotExist:
        return Response({"detail": "Mission inaccessible."}, status=status.HTTP_404_NOT_FOUND)
    return Response(EtapeMissionSerializer(mission.etapes.all(), many=True).data)

@api_view(["POST"])
@authentication_classes([RobotTokenAuthentication])
@permission_classes([IsRobotAuthenticated])
def robot_accuse_mission(request, mission_id):
    try: mission = Mission.objects.get(pk=mission_id, robot=request.user.robot); mission = enregistrer_accuse_reception(mission=mission)
    except Mission.DoesNotExist: return Response({"detail": "Mission inaccessible."}, status=404)
    except ErreurMission as exc: raise ValidationError({"detail": str(exc)})
    return Response(MissionSerializer(mission).data)

@api_view(["POST"])
@authentication_classes([RobotTokenAuthentication])
@permission_classes([IsRobotAuthenticated])
def robot_resultat_irrigation(request, irrigation_id):
    try: irrigation = Irrigation.objects.select_related("mesure_source__robot").get(pk=irrigation_id, mesure_source__robot=request.user.robot)
    except Irrigation.DoesNotExist: return Response({"detail": "Irrigation inaccessible."}, status=404)
    try: irrigation = enregistrer_resultat_irrigation(irrigation=irrigation, succes=request.data.get("succes"), duree_reelle=request.data.get("duree_reelle"), volume=request.data.get("volume"))
    except ErreurIrrigation as exc: raise ValidationError({"detail": str(exc)})
    return Response(IrrigationSerializer(irrigation).data)


@api_view(["GET"])
@authentication_classes([RobotTokenAuthentication])
@permission_classes([IsRobotAuthenticated])
def robot_commandes_irrigation(request):
    """Commandes déjà envoyées au robot, limitées à ses propres mesures."""
    operations = Irrigation.objects.filter(
        mesure_source__robot=request.user.robot,
        statut=Irrigation.Statut.COMMANDE_ENVOYEE,
    ).select_related("zone", "mission", "mesure_source")
    return Response(IrrigationSerializer(operations, many=True).data)
