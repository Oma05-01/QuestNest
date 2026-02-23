from django import forms
from .models import OrganisationVerification, PropertyVerification

class OrganisationVerificationForm(forms.ModelForm):
    class Meta:
        model = OrganisationVerification
        fields = ["document"]

class PropertyVerificationForm(forms.ModelForm):
    class Meta:
        model = PropertyVerification
        fields = ["documents"]
