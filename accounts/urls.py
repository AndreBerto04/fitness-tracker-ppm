from django.urls import path
from .views import SignUpView, CustomLoginView

urlpatterns = [
    # Login custom (override di quello di default) per usare il form con stile
    path("login/", CustomLoginView.as_view(), name="login"),
    # Registrazione nuovo atleta
    path("signup/", SignUpView.as_view(), name="signup"),
]
