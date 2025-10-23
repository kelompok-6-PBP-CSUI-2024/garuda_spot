from django import forms
from .models import Player, POS_CHOICES

_INPUT = "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none focus:ring-2 focus:ring-red-500"
_SELECT = "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none focus:ring-2 focus:ring-red-500"

class PlayerForm(forms.ModelForm):
    position1 = forms.ChoiceField(choices=POS_CHOICES, required=False, widget=forms.Select(attrs={"class": _SELECT}))
    position2 = forms.ChoiceField(choices=POS_CHOICES, required=False, widget=forms.Select(attrs={"class": _SELECT}))
    position3 = forms.ChoiceField(choices=POS_CHOICES, required=False, widget=forms.Select(attrs={"class": _SELECT}))

    class Meta:
        model = Player
        fields = [
            "name", "photo_url", "birth_date", "height_cm", "club",
            "position1", "position2", "position3",
            "caps", "goals", "assists"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": _INPUT}),
            "photo_url": forms.URLInput(attrs={"class": _INPUT}),
            "birth_date": forms.DateInput(attrs={"type": "date", "class": _INPUT}),
            "height_cm": forms.NumberInput(attrs={"min": 100, "step": 1, "class": _INPUT}),
            "club": forms.TextInput(attrs={"class": _INPUT}),
            "caps": forms.NumberInput(attrs={"min": 0, "class": _INPUT}),
            "goals": forms.NumberInput(attrs={"min": 0, "class": _INPUT}),
            "assists": forms.NumberInput(attrs={"min": 0, "class": _INPUT}),
        }
