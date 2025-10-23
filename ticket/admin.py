from django.contrib import admin
from .models import TicketMatch, TicketLink


@admin.register(TicketMatch)
class TicketMatchAdmin(admin.ModelAdmin):
    list_display = ("team1", "team2", "date")
    search_fields = ("team1", "team2")
    list_filter = ("date",)


@admin.register(TicketLink)
class TicketLinkAdmin(admin.ModelAdmin):
    list_display = ("vendor", "price", "match")
    search_fields = ("vendor",)
    list_filter = ("price",)

