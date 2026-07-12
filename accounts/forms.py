from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email", "age", "weight")
        labels = {
            "age": "Età",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["weight", "body_fat"]
        labels = {
            "weight": "Peso Corporeo (kg)",
            "body_fat": "Massa Grassa (%)",
        }
        widgets = {
            "weight": forms.NumberInput(attrs={"class": "form-control", "step": "0.1", "min": "0", "placeholder": "Es. 75"}),
            "body_fat": forms.NumberInput(attrs={"class": "form-control", "step": "0.1", "min": "0", "max": "100", "placeholder": "Es. 15"}),
        }


class CoachSettingsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["prezzo_mensile"]
        widgets = {
            "prezzo_mensile": forms.NumberInput(attrs={
                "class": "form-control", "step": "0.01", "min": "0"
            }),
        }
