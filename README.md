<<<<<<< HEAD
# RoboAgri-Kin

Robot agricole intelligent (ESP32) qui mesure l'humidité du sol, associé à une application Django de supervision.
Projet de Programmation III, L3 Sciences Informatiques, UCC.

## Installation du backend (Windows, PowerShell)

    cd backend
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py runserver

## Structure

- backend/ : application Django (parcelles, missions, mesures, irrigation, incidents)
- robot/ : code de l'ESP32
- frontend/ : interface web
- documentation/ : cahier des charges, conception BDD, diagrammes, rapports
=======
# Agro-Kin
Travail de programmation sur le robot arroseur
>>>>>>> e0832c41405f2a13e5daaf6d7b9501ad90f49862
