from django.contrib import admin
from django import forms

from .models import EtapeMission, Mission, Robot


class RobotAdminForm(forms.ModelForm):
    jeton = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Saisir un jeton lors de la création. Il est stocké sous forme de hachage.",
    )

    class Meta:
        model = Robot
        exclude = ("jeton_hash",)

    def clean_jeton(self):
        jeton = self.cleaned_data["jeton"]
        if not self.instance.pk and not jeton:
            raise forms.ValidationError("Un jeton dédié est obligatoire pour créer un robot.")
        return jeton

    def save(self, commit=True):
        robot = super().save(commit=False)
        jeton = self.cleaned_data.get("jeton")
        if jeton:
            robot.set_jeton(jeton)
        if commit:
            robot.save()
            self.save_m2m()
        return robot


@admin.register(Robot)
class RobotAdmin(admin.ModelAdmin):
    form = RobotAdminForm
    list_display = ("nom", "identifiant", "adresse_ip", "etat_connexion", "derniere_connexion")
    readonly_fields = ("identifiant",)
    search_fields = ("nom", "identifiant")


class EtapeMissionInline(admin.TabularInline):
    model = EtapeMission
    extra = 0


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ("id", "robot", "createur", "date_mission", "statut", "etat_transmission")
    list_filter = ("statut", "etat_transmission")
    inlines = (EtapeMissionInline,)


@admin.register(EtapeMission)
class EtapeMissionAdmin(admin.ModelAdmin):
    list_display = ("mission", "ordre", "zone", "statut")
    list_filter = ("statut",)
