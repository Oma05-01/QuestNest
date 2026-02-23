from django import forms
from .models import Tenancy

class TenancyForm(forms.ModelForm):
    class Meta:
        model = Tenancy
        fields = ["property", "tenant", "start_date", "end_date"]
