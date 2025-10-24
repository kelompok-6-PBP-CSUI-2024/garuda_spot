from django import forms
from .models import TicketMatch, TicketLink
import re

_SCHEME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9+\-.]*://')

def _normalize_url(u: str) -> str:
    if not u:
        return u
    u = u.strip()
    if not _SCHEME_RE.match(u):
        return 'https://' + u
    return u


class TicketMatchForm(forms.ModelForm):
    class Meta:
        model = TicketMatch
        fields = [
            "team1",
            "team2",
            "img_team1",
            "img_team2",
            "img_cup",
            "place",
            "date",
        ]

    def clean_team1(self):
        return (self.cleaned_data.get("team1") or "").strip()

    def clean_team2(self):
        return (self.cleaned_data.get("team2") or "").strip()

    def clean_place(self):
        val = (self.cleaned_data.get("place") or "").strip()
        return val or None


class TicketLinkForm(forms.ModelForm):
    class Meta:
        model = TicketLink
        fields = [
            "vendor",
            "vendor_link",
            "price",
            "img_vendor",
        ]

    def clean_vendor(self):
        return (self.cleaned_data.get("vendor") or "").strip()

