from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import FileResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

PAGES_FRONTEND = frozenset({
    "index",
    "parcelles",
    "robot",
    "mesures",
    "missions",
    "irrigation",
    "incidents",
    "historique",
    "rapports",
})

DOSSIERS_STATIQUES = frozenset({"css", "js", "vendor"})


def _fichier_sous(racine, chemin_relatif):
    racine = Path(racine).resolve()
    cible = (racine / chemin_relatif).resolve()
    if not cible.is_relative_to(racine) or not cible.is_file():
        raise Http404("Fichier introuvable.")
    return cible


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ConnexionView(LoginView):
    template_name = "connexion.html"
    redirect_authenticated_user = True


class DeconnexionView(LogoutView):
    next_page = "/connexion/"


@login_required
@ensure_csrf_cookie
@require_GET
def page_frontend(request, page="index"):
    """Sert une page HTML existante et pose le cookie CSRF pour fetch()."""
    if page not in PAGES_FRONTEND:
        raise Http404("Page inconnue.")
    fichier = _fichier_sous(settings.FRONTEND_DIR, f"{page}.html")
    return FileResponse(fichier.open("rb"), content_type="text/html; charset=utf-8")


@require_GET
def fichier_frontend(request, chemin, dossier):
    """CSS, JS et bibliothèques locales, accessibles aussi sur la page de connexion."""
    if dossier not in DOSSIERS_STATIQUES:
        raise Http404("Dossier interdit.")
    fichier = _fichier_sous(settings.FRONTEND_DIR / dossier, chemin)
    return FileResponse(fichier.open("rb"))
