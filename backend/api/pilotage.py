"""Relais HTTP vers le point d'accès ESP32 du robot agricole."""
import json
from http.client import HTTPConnection, HTTPException

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .permissions import IsOperatorOrAdmin


@api_view(["GET", "POST"])
@permission_classes([IsOperatorOrAdmin])
def pilotage(request):
    lecture = request.method in ("GET", "HEAD")
    chemin = "/status"
    if not lecture:
        code = request.data.get("move") if isinstance(request.data, dict) else None
        if code not in ("F", "B", "L", "R", "S"):
            return Response({"detail": "Direction inconnue."}, status=400)
        chemin = f"/cmd?move={code}"

    carte = HTTPConnection("192.168.4.1", timeout=1.5)
    try:
        carte.request("GET", chemin, headers={"Cache-Control": "no-store"})
        reponse = carte.getresponse()
        if not 200 <= reponse.status < 300:
            raise ValueError("Réponse refusée")
        if lecture:
            donnees = json.loads(reponse.read(4097))
            if not isinstance(donnees, dict) or not isinstance(donnees.get("etat"), str) or not donnees["etat"].strip():
                raise ValueError("État absent")
            return Response({"etat": donnees["etat"]}, headers={"Cache-Control": "no-store"})
        return Response(status=204)
    except (OSError, HTTPException, ValueError):
        return Response({"detail": "Aucune confirmation de l’ESP32. Vérifiez le Wi-Fi du poste serveur."}, status=502)
    finally:
        carte.close()
