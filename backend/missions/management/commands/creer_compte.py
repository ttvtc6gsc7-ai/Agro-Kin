from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crée ou met à jour un compte de démonstration et lui attribue un rôle."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--password", required=True)
        parser.add_argument("--role", choices=("Administrateur", "Operateur"), required=True)

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name=options["role"])
        user, created = get_user_model().objects.get_or_create(username=options["username"])
        user.set_password(options["password"])
        user.save()
        user.groups.add(group)
        self.stdout.write(self.style.SUCCESS(f"{options['username']} : {'créé' if created else 'mis à jour'} ({group.name})"))
