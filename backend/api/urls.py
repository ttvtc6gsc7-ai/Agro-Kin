from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("cultures", views.CultureViewSet)
router.register("parcelles", views.ParcelleViewSet)
router.register("zones", views.ZoneViewSet)
router.register("seuils", views.SeuilViewSet)
router.register("robots", views.RobotViewSet)
router.register("missions", views.MissionViewSet)
router.register("etapes", views.EtapeMissionViewSet)
router.register("etalonnages", views.EtalonnageViewSet)
router.register("recommandations", views.RecommandationViewSet)
router.register("irrigations", views.IrrigationViewSet)
router.register("incidents", views.IncidentViewSet)

urlpatterns = [
    path("auth/me/", views.me), path("utilisateurs/", views.users), path("tableau-de-bord/", views.dashboard), path("rapports/", views.rapport),
    path("robot/mesures/", views.robot_mesures), path("robot/missions/", views.robot_missions),
    path("robot/missions/<int:mission_id>/etapes/", views.robot_etapes_mission), path("robot/missions/<int:mission_id>/accuse/", views.robot_accuse_mission),
    path("robot/irrigations/", views.robot_commandes_irrigation), path("robot/irrigations/<int:irrigation_id>/resultat/", views.robot_resultat_irrigation), path("", include(router.urls)),
]
