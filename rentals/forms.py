from django import forms
from .models import Tenancy

class TenancyForm(forms.ModelForm):
    class Meta:
        model = Tenancy
        fields = ["unit", "tenant", "start_date", "end_date"]
