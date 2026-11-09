from django.contrib import admin

from .models import Irrigation, RecommandationIrrigation


@admin.register(RecommandationIrrigation)
class RecommandationIrrigationAdmin(admin.ModelAdmin):
    list_display = ("id", "zone", "mesure_source", "duree_max", "autorisee_par", "autorisee_le")
    list_filter = ("zone",)


@admin.register(Irrigation)
class IrrigationAdmin(admin.ModelAdmin):
    list_display = ("operation_id", "zone", "mesure_source", "duree_max", "statut", "date_irrigation")
    list_filter = ("statut",)
    readonly_fields = ("operation_id",)
