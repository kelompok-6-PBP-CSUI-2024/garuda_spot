from django.core.management.base import BaseCommand
from datetime import date, timedelta

from ticket.models import TicketMatch, TicketLink


class Command(BaseCommand):
    help = "Seed 3 TicketMatch with 2 TicketLink each (idempotent)."

    def handle(self, *args, **options):
        base = date.today()
        matches = [
            {
                "team1": "Garuda A",
                "team2": "Garuda B",
                "date": base,
                "img_team1": "https://picsum.photos/seed/a/200",
                "img_team2": "https://picsum.photos/seed/b/200",
                "img_arena": "https://picsum.photos/seed/arena1/400/200",
            },
            {
                "team1": "Garuda C",
                "team2": "Garuda D",
                "date": base + timedelta(days=1),
                "img_team1": "https://picsum.photos/seed/c/200",
                "img_team2": "https://picsum.photos/seed/d/200",
                "img_arena": "https://picsum.photos/seed/arena2/400/200",
            },
            {
                "team1": "Garuda E",
                "team2": "Garuda F",
                "date": base + timedelta(days=2),
                "img_team1": "https://picsum.photos/seed/e/200",
                "img_team2": "https://picsum.photos/seed/f/200",
                "img_arena": "https://picsum.photos/seed/arena3/400/200",
            },
        ]

        created_matches = []
        for idx, m in enumerate(matches, start=1):
            match, created = TicketMatch.objects.get_or_create(
                team1=m["team1"],
                team2=m["team2"],
                date=m["date"],
                defaults={
                    "img_team1": m["img_team1"],
                    "img_team2": m["img_team2"],
                    "img_arena": m["img_arena"],
                },
            )
            if not created:
                # Keep data fresh
                match.img_team1 = m["img_team1"]
                match.img_team2 = m["img_team2"]
                match.img_arena = m["img_arena"]
                match.save()

            links_data = [
                (
                    "Vendor A",
                    f"https://vendor.example.com/{idx}/a",
                    100000 + idx * 1000,
                    "https://picsum.photos/seed/vendorA/100",
                ),
                (
                    "Vendor B",
                    f"https://vendor.example.com/{idx}/b",
                    200000 + idx * 1000,
                    "https://picsum.photos/seed/vendorB/100",
                ),
            ]

            for vendor, link, price, img in links_data:
                TicketLink.objects.get_or_create(
                    match=match,
                    vendor=vendor,
                    vendor_link=link,
                    defaults={"price": price, "img_vendor": img},
                )

            created_matches.append(match.id)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded/updated TicketMatch IDs: {created_matches}"
        ))

