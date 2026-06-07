from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


# SignUp (Slide 24): estende UserCreationForm per il nostro CustomUser
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email", "age", "weight")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Stile Bootstrap su tutti i campi (incluse password1/password2)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


# Login (Slide 19): AuthenticationForm con stile Bootstrap
class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})
