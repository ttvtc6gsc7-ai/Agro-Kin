from django.contrib import admin

from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("type_incident", "date_incident", "statut", "mission", "mesure", "robot")
    list_filter = ("statut", "type_incident")
    search_fields = ("description",)
    readonly_fields = ("message_id",)
