from django.core.management.base import BaseCommand

from merch.models import Merch


class Command(BaseCommand):
    help = "Seed a few dummy merchandise items (idempotent)."

    def handle(self, *args, **options):
        items = [
            {
                "name": "Garuda Home Jersey 2025",
                "vendor": "Official Store",
                "price": 450000,
                "stock": 25,
                "description": "Home kit with breathable fabric and authentic crest.",
                "thumbnail": "https://picsum.photos/seed/jersey/400/400",
                "category": "jersey",
                "link": "https://example.com/garuda-home-2025",
            },
            {
                "name": "Garuda Scarf Limited",
                "vendor": "Supporter Merch",
                "price": 120000,
                "stock": 50,
                "description": "Soft acrylic scarf with double-sided Garuda print.",
                "thumbnail": "https://picsum.photos/seed/scarf/400/400",
                "category": "scarf",
                "link": "https://example.com/garuda-scarf",
            },
            {
                "name": "Garuda Cap Classic",
                "vendor": "Fan Gear",
                "price": 95000,
                "stock": 40,
                "description": "Adjustable cap with embroidered crest.",
                "thumbnail": "https://picsum.photos/seed/cap/400/400",
                "category": "cap",
                "link": "https://example.com/garuda-cap",
            },
            {
                "name": "Garuda Hoodie Red",
                "vendor": "Fan Gear",
                "price": 275000,
                "stock": 30,
                "description": "Fleece-lined hoodie for matchday comfort.",
                "thumbnail": "https://picsum.photos/seed/hoodie/400/400",
                "category": "hoodie",
                "link": "https://example.com/garuda-hoodie",
            },
        ]

        created = []
        for data in items:
            merch, was_created = Merch.objects.update_or_create(
                name=data["name"],
                defaults=data,
            )
            created.append((merch.name, was_created))

        summary = ", ".join([f"{name} ({'created' if flag else 'updated'})" for name, flag in created])
        self.stdout.write(self.style.SUCCESS(f"Seeded merch: {summary}"))
