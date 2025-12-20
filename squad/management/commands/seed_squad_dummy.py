from datetime import date, timedelta

from django.core.management.base import BaseCommand

from squad.models import Player


class Command(BaseCommand):
    help = "Seed dummy squad players (idempotent)."

    def handle(self, *args, **options):
        today = date.today()
        items = [
            {
                "name": "Nadeo Argawinata",
                "photo_url": "https://picsum.photos/seed/nadeo/200",
                "birth_date": today - timedelta(days=28 * 365),
                "club": "Bali United",
                "height_cm": 187,
                "position1": "GK",
                "caps": 45,
                "goals": 0,
                "assists": 0,
            },
            {
                "name": "Jordi Amat",
                "photo_url": "https://picsum.photos/seed/jordi/200",
                "birth_date": today - timedelta(days=32 * 365),
                "club": "Johor Darul Ta'zim",
                "height_cm": 184,
                "position1": "CB",
                "caps": 28,
                "goals": 1,
                "assists": 2,
            },
            {
                "name": "Asnawi Mangkualam",
                "photo_url": "https://picsum.photos/seed/asnawi/200",
                "birth_date": today - timedelta(days=24 * 365),
                "club": "Jeonnam Dragons",
                "height_cm": 174,
                "position1": "RB",
                "position2": "RWB",
                "caps": 30,
                "goals": 2,
                "assists": 5,
            },
            {
                "name": "Marselino Ferdinan",
                "photo_url": "https://picsum.photos/seed/marselino/200",
                "birth_date": today - timedelta(days=20 * 365),
                "club": "KMSK Deinze",
                "height_cm": 176,
                "position1": "CAM",
                "position2": "LW",
                "caps": 18,
                "goals": 4,
                "assists": 6,
            },
            {
                "name": "Rafael Struick",
                "photo_url": "https://picsum.photos/seed/struick/200",
                "birth_date": today - timedelta(days=21 * 365),
                "club": "ADO Den Haag",
                "height_cm": 186,
                "position1": "ST",
                "position2": "LW",
                "caps": 15,
                "goals": 5,
                "assists": 3,
            },
        ]

        created = []
        for data in items:
            player, was_created = Player.objects.update_or_create(
                name=data["name"],
                defaults=data,
            )
            created.append((player.name, was_created))

        summary = ", ".join([f"{name} ({'created' if flag else 'updated'})" for name, flag in created])
        self.stdout.write(self.style.SUCCESS(f"Seeded players: {summary}"))
