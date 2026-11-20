from django.contrib import admin

from .models import Culture, Parcelle, Seuil, Zone


@admin.register(Culture)
class CultureAdmin(admin.ModelAdmin):
    list_display = ("nom", "type_culture")
    search_fields = ("nom", "type_culture")


class ZoneInline(admin.TabularInline):
    model = Zone
    extra = 0


@admin.register(Parcelle)
class ParcelleAdmin(admin.ModelAdmin):
    list_display = ("nom", "superficie", "localisation")
    search_fields = ("nom", "localisation")
    inlines = (ZoneInline,)


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("nom", "parcelle", "culture")
    list_filter = ("parcelle", "culture")
    search_fields = ("nom",)


@admin.register(Seuil)
class SeuilAdmin(admin.ModelAdmin):
    list_display = ("zone", "valeur_min", "valeur_max", "duree_max_arrosage", "actif", "date_configuration")
    list_filter = ("actif",)
