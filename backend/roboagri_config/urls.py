"""
URL configuration for roboagri_config project.
"""
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("connexion/", views.ConnexionView.as_view(), name="login"),
    path("deconnexion/", views.DeconnexionView.as_view(), name="logout"),
    path("", views.page_frontend, name="frontend-index"),
    path("<str:page>.html", views.page_frontend, name="frontend-page"),
    path("css/<path:chemin>", views.fichier_frontend, {"dossier": "css"}),
    path("js/<path:chemin>", views.fichier_frontend, {"dossier": "js"}),
    path("vendor/<path:chemin>", views.fichier_frontend, {"dossier": "vendor"}),
]
