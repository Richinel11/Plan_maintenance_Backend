from django.core.management.base import BaseCommand


ENTITES = [
    {"name": "Production",   "type": "PROD"},
    {"name": "Transport",    "type": "TRANS"},
    {"name": "Distribution", "type": "DIST"},
]


class Command(BaseCommand):
    help = "Seed des 3 EntiteMetier de base (Production, Transport, Distribution)"

    def handle(self, *args, **kwargs):
        from user.models import EntiteMetier

        for data in ENTITES:
            _, created = EntiteMetier.objects.get_or_create(
                name=data["name"],
                defaults={"type": data["type"]},
            )
            status = "[+] créée" if created else "[ ] déjà existante"
            self.stdout.write(f"  {status} : {data['name']} ({data['type']})")

        self.stdout.write(self.style.SUCCESS("\nSeed EntiteMetier terminé."))
