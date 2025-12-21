from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from schedule.models import NationalTeamSchedule


class Command(BaseCommand):
    help = "Seed dummy matches for schedule (idempotent)."

    def handle(self, *args, **options):
        now = datetime.now()
        items = [
            {
                "home_team": "Indonesia",
                "away_team": "Vietnam",
                "location": "Gelora Bung Karno",
                "match_date": now + timedelta(days=3),
                "category": "FIFA Matchday A",
            },
            {
                "home_team": "Indonesia",
                "away_team": "Thailand",
                "location": "Stadion Pakansari",
                "match_date": now + timedelta(days=10),
                "category": "AFF Championship",
            },
            {
                "home_team": "Indonesia",
                "away_team": "Malaysia",
                "location": "Bukit Jalil",
                "match_date": now + timedelta(days=17),
                "category": "Friendly Match",
            },
        ]

        created = []
        for data in items:
            match, was_created = NationalTeamSchedule.objects.update_or_create(
                home_team=data["home_team"],
                away_team=data["away_team"],
                match_date=data["match_date"],
                defaults=data,
            )
            created.append((f"{match.home_team} vs {match.away_team}", was_created))

        summary = ", ".join([f"{name} ({'created' if flag else 'updated'})" for name, flag in created])
        self.stdout.write(self.style.SUCCESS(f"Seeded matches: {summary}"))
