from django.urls import path
from .views import (
    SignUpView, CustomLoginView,
    CoachListView, CoachSettingsView,
    SendSubscriptionRequestView, AcceptRequestView, RejectRequestView,
    TerminateSubscriptionView,
)

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("signup/", SignUpView.as_view(), name="signup"),

    path("coaches/", CoachListView.as_view(), name="coach_list"),
    path("coaches/<int:coach_id>/richiedi/", SendSubscriptionRequestView.as_view(), name="send_subscription"),
    path("impostazioni/", CoachSettingsView.as_view(), name="coach_settings"),

    path("richieste/<int:req_id>/accetta/", AcceptRequestView.as_view(), name="accept_request"),
    path("richieste/<int:req_id>/rifiuta/", RejectRequestView.as_view(), name="reject_request"),

    path("abbonamento/<int:athlete_id>/interrompi/", TerminateSubscriptionView.as_view(), name="terminate_subscription"),
]
