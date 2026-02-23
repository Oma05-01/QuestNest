from django import forms
from .models import User

class EmailForm(forms.Form):
    email = forms.EmailField()

class PasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    organisation_name = forms.CharField(max_length=255)

    class Meta:
        model = User
        fields = ["name", "email", "password"]

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name"]