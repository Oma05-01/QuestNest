from django import forms
from .models import Organisation


class OrganisationCreateForm(forms.ModelForm):
    class Meta:
        model = Organisation
        fields = ["name"]
