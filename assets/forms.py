from django import forms
from .models import Assets

class AssetsForm(forms.ModelForm):
    class Meta:
        model = Assets
        fields = ['name', 'location']
