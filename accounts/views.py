from datetime import timedelta
from django.utils import timezone
from django.urls import reverse_lazy
from django.views import generic, View
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CoachSettingsForm
from .models import CustomUser, SubscriptionRequest


# SignUp (Slide 25): CBV CreateView che usa il form custom e rimanda al login
class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


# Login (Slide 19): LoginView con form custom per mostrare gli errori con stile
class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = "registration/login.html"


# MARKETPLACE: l'atleta sfoglia i coach disponibili con il loro prezzo
class CoachListView(LoginRequiredMixin, generic.ListView):
    model = CustomUser
    template_name = "accounts/coach_list.html"
    context_object_name = "coaches"

    def dispatch(self, request, *args, **kwargs):
        # Solo gli atleti accedono al marketplace
        if request.user.is_authenticated and request.user.is_coach:
            raise PermissionDenied("Sezione riservata agli atleti.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Libera l'atleta se l'abbonamento è scaduto, così può rifare richieste
        request.user.refresh_subscription_status()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return CustomUser.objects.filter(is_coach=True).order_by('prezzo_mensile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Coach verso cui l'atleta ha gia' una richiesta PENDING
        context['pending_coach_ids'] = list(
            SubscriptionRequest.objects.filter(
                atleta=self.request.user, status='PENDING'
            ).values_list('coach_id', flat=True)
        )
        return context


# IMPOSTAZIONI COACH: modifica del prezzo mensile
class CoachSettingsView(LoginRequiredMixin, generic.UpdateView):
    form_class = CoachSettingsForm
    template_name = "accounts/coach_settings.html"
    success_url = reverse_lazy("coach_settings")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_coach:
            raise PermissionDenied("Sezione riservata ai coach.")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        # Il coach modifica sempre se stesso
        return self.request.user


# ATLETA invia una richiesta di abbonamento a un coach
class SendSubscriptionRequestView(LoginRequiredMixin, View):
    def post(self, request, coach_id):
        # Libera l'atleta se l'abbonamento precedente è scaduto
        request.user.refresh_subscription_status()
        # RBAC: solo atleti senza coach possono inviare richieste
        if request.user.is_coach or request.user.coach is not None:
            raise PermissionDenied("Non puoi inviare richieste di abbonamento.")
        coach = get_object_or_404(CustomUser, id=coach_id, is_coach=True)
        # Evita richieste PENDING duplicate verso lo stesso coach
        already = SubscriptionRequest.objects.filter(
            atleta=request.user, coach=coach, status='PENDING'
        ).exists()
        if not already:
            SubscriptionRequest.objects.create(atleta=request.user, coach=coach)
        return redirect('coach_list')


# COACH accetta una richiesta -> associa l'atleta
class AcceptRequestView(LoginRequiredMixin, View):
    def post(self, request, req_id):
        if not request.user.is_coach:
            raise PermissionDenied("Sezione riservata ai coach.")
        sub = get_object_or_404(SubscriptionRequest, id=req_id, coach=request.user, status='PENDING')
        sub.status = 'ACCEPTED'
        # Abbonamento valido 30 giorni dalla data di accettazione
        sub.data_scadenza = timezone.now().date() + timedelta(days=30)
        sub.save()
        # Associazione ufficiale nel DB
        athlete = sub.atleta
        athlete.coach = request.user
        athlete.save()
        return redirect('workout_list')


# COACH rifiuta una richiesta
class RejectRequestView(LoginRequiredMixin, View):
    def post(self, request, req_id):
        if not request.user.is_coach:
            raise PermissionDenied("Sezione riservata ai coach.")
        sub = get_object_or_404(SubscriptionRequest, id=req_id, coach=request.user, status='PENDING')
        sub.status = 'REJECTED'
        sub.save()
        return redirect('workout_list')


# INTERRUZIONE RAPPORTO (divorzio) - usabile da atleta o coach
class TerminateSubscriptionView(LoginRequiredMixin, View):
    def post(self, request, athlete_id):
        athlete = get_object_or_404(CustomUser, id=athlete_id, is_coach=False)
        # Autorizzazione: o è l'atleta stesso, o è il suo coach attuale
        if request.user.id != athlete.id and athlete.coach_id != request.user.id:
            raise PermissionDenied("Non puoi interrompere questo rapporto.")

        coach = athlete.coach
        # Annulla l'abbonamento attivo e libera l'atleta
        SubscriptionRequest.objects.filter(
            atleta=athlete, coach=coach, status='ACCEPTED'
        ).update(status='CANCELLED')
        athlete.coach = None
        athlete.save()

        # Redirect coerente col ruolo
        if request.user.is_coach:
            return redirect('workout_list')
        return redirect('coach_list')
