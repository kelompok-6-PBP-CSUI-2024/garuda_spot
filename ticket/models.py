from django.db import models
import uuid


class TicketMatch(models.Model):
    match_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    team1 = models.CharField(max_length=100)
    team2 = models.CharField(max_length=100)
    img_team1 = models.URLField()
    img_team2 = models.URLField()
    img_cup = models.URLField(blank=True, null=True)
    place = models.CharField(max_length=255, null=True)
    date = models.DateField()

    class Meta:
        ordering = ["-match_id"]


    def __str__(self) -> str:
        return f"{self.team1} vs {self.team2} on {self.date}"


class TicketLink(models.Model):
    link_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    vendor = models.CharField(max_length=100)
    vendor_link = models.URLField()
    price = models.IntegerField()
    img_vendor = models.URLField()
    match = models.ForeignKey(TicketMatch, on_delete=models.CASCADE, related_name="links")

    class Meta:
        ordering = ["-link_id"]


    def __str__(self) -> str:
        return f"{self.vendor} - {self.match}"
