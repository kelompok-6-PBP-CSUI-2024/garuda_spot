from django.forms import ModelForm
from merch.models import Merch

class MerchForm(ModelForm):
    class Meta:
        model = Merch
        fields = ["name", "vendor", "price", "stock", "description", "thumbnail", "category", "link"]