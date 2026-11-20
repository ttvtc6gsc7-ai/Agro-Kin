from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crée de façon idempotente les groupes Administrateur et Operateur."

    def handle(self, *args, **options):
        for name in ("Administrateur", "Operateur"):
            _, created = Group.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS(f"{name} : {'créé' if created else 'déjà présent'}"))
