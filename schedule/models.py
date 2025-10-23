from django.utils import timezone
import uuid
from django.db import models

MATCH_CATEGORY_CHOICES = (
    ('FIFA Matchday A', 'FIFA Matchday A'),
    ('FIFA Matchday B', 'FIFA Matchday B'),
    ('AFF Championship', 'AFF Championship'),
    ('AFC Qualifiers', 'AFC Qualifiers'),
    ('AFC Cup', 'AFC Cup'),
    ('World Cup Qualifiers', 'World Cup Qualifiers'),
    ('World Cup', 'World Cup'),
    ('Other', 'Other'),
)

class NationalTeamSchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    home_team = models.CharField(max_length=100, default="Indonesia")
    away_team = models.CharField(max_length=100)
    home_code = models.CharField(max_length=3, blank=True, null=True)
    away_code = models.CharField(max_length=3, blank=True, null=True)
    match_date = models.DateTimeField()
    location = models.CharField(max_length=150)
    category = models.CharField(
        max_length=20,
        choices=MATCH_CATEGORY_CHOICES,
        default=MATCH_CATEGORY_CHOICES[0][0]
    )
    home_score = models.PositiveSmallIntegerField(null=True, blank=True)
    away_score = models.PositiveSmallIntegerField(null=True, blank=True)
    lineup = models.TextField(null=True, blank=True)
    review = models.TextField(null=True, blank=True)


    shots_home = models.PositiveSmallIntegerField(null=True, blank=True)
    shots_away = models.PositiveSmallIntegerField(null=True, blank=True)

    shots_on_target_home = models.PositiveSmallIntegerField(null=True, blank=True)
    shots_on_target_away = models.PositiveSmallIntegerField(null=True, blank=True)

    possession_home = models.PositiveSmallIntegerField(null=True, blank=True)
    possession_away = models.PositiveSmallIntegerField(null=True, blank=True)

    passes_home = models.PositiveIntegerField(null=True, blank=True)
    passes_away = models.PositiveIntegerField(null=True, blank=True)

    pass_accuracy_home = models.PositiveSmallIntegerField(null=True, blank=True)
    pass_accuracy_away = models.PositiveSmallIntegerField(null=True, blank=True)

    fouls_home = models.PositiveSmallIntegerField(null=True, blank=True)
    fouls_away = models.PositiveSmallIntegerField(null=True, blank=True)

    yellow_cards_home = models.PositiveSmallIntegerField(null=True, blank=True)
    yellow_cards_away = models.PositiveSmallIntegerField(null=True, blank=True)

    red_cards_home = models.PositiveSmallIntegerField(null=True, blank=True)
    red_cards_away = models.PositiveSmallIntegerField(null=True, blank=True)

    offsides_home = models.PositiveSmallIntegerField(null=True, blank=True)
    offsides_away = models.PositiveSmallIntegerField(null=True, blank=True)

    corners_home = models.PositiveSmallIntegerField(null=True, blank=True)
    corners_away = models.PositiveSmallIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-match_date"]
        verbose_name = "National Team Schedule"
        verbose_name_plural = "National Team Schedules"

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} - {self.get_category_display()}"

    @property
    def category_image_url(self):
        category_images = {
            'FIFA Matchday A': '',
            'FIFA Matchday B': '',
            'AFF Championship': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/08/ASEAN_Mitsubishi_Electric_Cup_2024_logo.svg/1200px-ASEAN_Mitsubishi_Electric_Cup_2024_logo.svg.png',
            'AFC Qualifiers': 'https://upload.wikimedia.org/wikipedia/id/4/4d/AFC_Asian_Cup.png',
            'AFC Cup': 'https://upload.wikimedia.org/wikipedia/id/4/4d/AFC_Asian_Cup.png',
            'World Cup Qualifiers': 'https://brandlogos.net/wp-content/uploads/2023/08/2026-FIFA-World-Cup-logo.png',
            'World Cup': 'https://brandlogos.net/wp-content/uploads/2023/08/2026-FIFA-World-Cup-logo.png',
            'Other': 'https://example.com/images/other.png',
        }
        return category_images.get(self.category, category_images['Other'])

    @property
    def is_upcoming(self):
        return self.match_date > timezone.now()
