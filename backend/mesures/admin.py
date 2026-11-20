from django.contrib import admin

from .models import Etalonnage, Mesure


@admin.register(Etalonnage)
class EtalonnageAdmin(admin.ModelAdmin):
    list_display = ("robot", "valeur_min", "valeur_max", "etat", "date_etalonnage")
    list_filter = ("etat",)


@admin.register(Mesure)
class MesureAdmin(admin.ModelAdmin):
    list_display = ("id", "zone", "mission", "robot", "humidite", "est_valide", "statut", "date_heure")
    list_filter = ("est_valide", "statut")
    search_fields = ("message_id",)
    readonly_fields = ("message_id",)
