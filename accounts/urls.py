from django.urls import path
from .views import (
    SignUpView, CustomLoginView,
    CoachListView, CoachSettingsView,
    SendSubscriptionRequestView, AcceptRequestView, RejectRequestView,
    TerminateSubscriptionView,
)

urlpatterns = [
    # Login custom (override di quello di default) per usare il form con stile
    path("login/", CustomLoginView.as_view(), name="login"),
    # Registrazione nuovo atleta
    path("signup/", SignUpView.as_view(), name="signup"),

    # Marketplace abbonamenti
    path("coaches/", CoachListView.as_view(), name="coach_list"),
    path("coaches/<int:coach_id>/richiedi/", SendSubscriptionRequestView.as_view(), name="send_subscription"),
    path("impostazioni/", CoachSettingsView.as_view(), name="coach_settings"),

    # Gestione richieste lato coach
    path("richieste/<int:req_id>/accetta/", AcceptRequestView.as_view(), name="accept_request"),
    path("richieste/<int:req_id>/rifiuta/", RejectRequestView.as_view(), name="reject_request"),

    # Interruzione rapporto (atleta o coach)
    path("abbonamento/<int:athlete_id>/interrompi/", TerminateSubscriptionView.as_view(), name="terminate_subscription"),
]
