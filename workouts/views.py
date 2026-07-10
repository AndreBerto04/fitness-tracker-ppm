from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from accounts.models import CustomUser, SubscriptionRequest
from accounts.forms import ProfileForm
from .models import WorkoutLog, ExerciseSession, ExerciseSet, Goal
from .forms import WorkoutLogForm, ExerciseSessionForm, ExerciseSetForm, GoalForm


# 1. LISTA STORICO (Read) - con biforcazione RBAC Coach/Atleta
class WorkoutListView(LoginRequiredMixin, ListView):
    model = WorkoutLog
    template_name = 'workouts/workout_list.html'
    context_object_name = 'workouts'

    def get(self, request, *args, **kwargs):
        # RBAC: il Coach vede la dashboard dei suoi atleti + le richieste in attesa
        if request.user.is_coach:
            # Scadenza 30gg: libera gli atleti con abbonamento scaduto
            for athlete in request.user.athletes.all():
                athlete.refresh_subscription_status()
            pending_requests = SubscriptionRequest.objects.filter(
                coach=request.user, status='PENDING'
            )
            return render(request, 'workouts/coach_dashboard.html', {
                'athletes': request.user.athletes.all(),
                'pending_requests': pending_requests,
            })
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # RBAC: l'atleta vede solo i propri allenamenti
        return WorkoutLog.objects.filter(user=self.request.user).order_by('-date')


# 2. CREAZIONE NUOVO ALLENAMENTO (Create - Passo 1)
class WorkoutCreateView(LoginRequiredMixin, CreateView):
    model = WorkoutLog
    form_class = WorkoutLogForm
    template_name = 'workouts/workout_form.html'

    def form_valid(self, form):
        # Lega l'allenamento all'utente loggato prima del salvataggio
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        # Dopo la creazione si va all'hub di editing per aggiungere esercizi/serie
        return reverse('workout_edit', kwargs={'pk': self.object.pk})


# 3. DETTAGLIO HUB E AGGIUNTA SERIE (Create - Passo 2)
class WorkoutDetailView(LoginRequiredMixin, DetailView):
    model = WorkoutLog
    template_name = 'workouts/workout_detail.html'
    context_object_name = 'workout'

    def get_queryset(self):
        # RBAC: accedono il proprietario del log OPPURE il suo coach associato
        return WorkoutLog.objects.filter(
            Q(user=self.request.user) | Q(user__coach=self.request.user)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workout = self.object

        total_volume = 0.0
        muscle_sets = {}  # muscolo -> n. serie totali

        for exercise in workout.exercises.all():
            sets = list(exercise.sets.all())
            n_sets = len(sets)

            # Resoconto muscolare: conteggio lineare delle serie sull'UNICO muscolo target
            muscle = exercise.get_target_muscle()
            muscle_sets[muscle] = muscle_sets.get(muscle, 0) + n_sets

            # Volume totale = somma di reps * peso (solo forza)
            for s in sets:
                if s.reps and s.weight:
                    total_volume += s.reps * float(s.weight)

        # Costruzione del report con livello di stimolo, colore e larghezza barra
        muscle_report = []
        for muscle, n in sorted(muscle_sets.items(), key=lambda x: x[1], reverse=True):
            if n >= 5:
                level, color = 'Alto', 'bg-danger'
            elif n >= 3:
                level, color = 'Medio', 'bg-warning'
            else:
                level, color = 'Leggero', 'bg-success'
            muscle_report.append({
                'muscle': muscle,
                'sets': n,
                'level': level,
                'color': color,
                'width': min(int(n / 6 * 100), 100),
            })

        context['total_volume'] = round(total_volume, 1)
        context['muscle_report'] = muscle_report
        return context


# 3-bis. HUB DI EDITING (aggiunta esercizi e serie) - sola scrittura
class WorkoutEditView(LoginRequiredMixin, DetailView):
    model = WorkoutLog
    template_name = 'workouts/workout_edit.html'
    context_object_name = 'workout'

    def get_queryset(self):
        # RBAC: si modificano solo i propri allenamenti
        return WorkoutLog.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        workout = self.object
        action_type = request.POST.get('action_type')

        # CASO 1: creazione dell'esercizio tramite ModelForm (validazione nativa)
        if action_type == 'create_exercise':
            form = ExerciseSessionForm(request.POST)
            if form.is_valid():
                exercise = form.save(commit=False)
                exercise.workout_log = workout
                exercise.save()
            else:
                context = self.get_context_data()
                context['exercise_form'] = form
                return self.render_to_response(context)

        # CASO 2: aggiunta di una serie tramite ModelForm
        elif action_type == 'add_set':
            exercise = get_object_or_404(
                ExerciseSession, id=request.POST.get('exercise_id'), workout_log=workout
            )
            form = ExerciseSetForm(request.POST)
            if form.is_valid():
                exercise_set = form.save(commit=False)
                exercise_set.exercise_session = exercise
                exercise_set.save()
            else:
                context = self.get_context_data()
                context['set_form'] = form
                return self.render_to_response(context)

        return redirect('workout_edit', pk=workout.pk)


# 4. MODIFICA TITOLO ALLENAMENTO (Update)
class WorkoutUpdateView(LoginRequiredMixin, UpdateView):
    model = WorkoutLog
    form_class = WorkoutLogForm
    template_name = 'workouts/workout_form.html'

    def get_queryset(self):
        # RBAC: si modificano solo i propri allenamenti
        return WorkoutLog.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def get_success_url(self):
        # Intercettiamo quale pulsante è stato premuto nel form
        if self.request.POST.get('save_mode') == 'quick_save':
            return reverse('workout_list')
        # "Modifica Esercizi" porta all'hub di editing
        return reverse('workout_edit', kwargs={'pk': self.object.pk})


# 5. CANCELLAZIONE ALLENAMENTO (Delete)
class WorkoutDeleteView(LoginRequiredMixin, DeleteView):
    model = WorkoutLog
    template_name = 'workouts/workout_confirm_delete.html'
    context_object_name = 'workout'
    success_url = reverse_lazy('workout_list')

    def get_queryset(self):
        # RBAC: si eliminano solo i propri allenamenti
        return WorkoutLog.objects.filter(user=self.request.user)


# 6. ELIMINA UN INTERO ESERCIZIO (e le sue serie)
# Richiesta POST: eliminare cambia lo stato del sistema (slide "GET and POST")
class ExerciseDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        exercise = get_object_or_404(ExerciseSession, pk=pk, workout_log__user=request.user)
        workout_pk = exercise.workout_log.pk
        exercise.delete()
        return redirect('workout_edit', pk=workout_pk)


# 7. ELIMINA UNA SINGOLA SERIE
# Richiesta POST: eliminare cambia lo stato del sistema (slide "GET and POST")
class SetDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        set_obj = get_object_or_404(ExerciseSet, pk=pk, exercise_session__workout_log__user=request.user)
        workout_pk = set_obj.exercise_session.workout_log.pk
        set_obj.delete()
        return redirect('workout_edit', pk=workout_pk)


# 8. DASHBOARD OBIETTIVI (Read + Create obiettivi suggeriti)
class GoalListView(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'workouts/goal_list.html'
    context_object_name = 'goals'

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Suggerimenti dinamici calcolati sul peso corporeo
        if hasattr(self.request.user, 'get_suggested_goals'):
            context['suggested_goals'] = self.request.user.get_suggested_goals()
        else:
            context['suggested_goals'] = []
        # Form sempre disponibili in pagina
        context.setdefault('goal_form', GoalForm())
        context.setdefault('profile_form', ProfileForm(instance=self.request.user))
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        self.object_list = self.get_queryset()

        # CASO A: aggiornamento dati antropometrici (peso + massa grassa)
        if action == 'update_profile':
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                return redirect('goal_list')
            context = self.get_context_data(profile_form=profile_form)
            return self.render_to_response(context)

        # CASO B: creazione di un nuovo obiettivo (validazione nativa)
        goal_form = GoalForm(request.POST)
        if goal_form.is_valid():
            goal = goal_form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('goal_list')
        context = self.get_context_data(goal_form=goal_form)
        return self.render_to_response(context)


# 8-bis. ELIMINA OBIETTIVO
class GoalDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        goal = get_object_or_404(Goal, pk=pk, user=request.user)
        goal.delete()
        return redirect('goal_list')


# 8-ter. SEGNA OBIETTIVO COME COMPLETATO/NON COMPLETATO
class GoalCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        goal = get_object_or_404(Goal, pk=pk, user=request.user)
        goal.is_completed = not goal.is_completed
        goal.save()
        return redirect('goal_list')


# 9. DETTAGLIO ATLETA PER IL COACH (Read log + Update coach_feedback)
class CoachAthleteDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'workouts/coach_athlete_detail.html'
    context_object_name = 'athlete'
    pk_url_kwarg = 'athlete_id'

    def dispatch(self, request, *args, **kwargs):
        # RBAC: 403 se l'utente loggato non è un coach (feedback chiaro di permesso negato)
        if request.user.is_authenticated and not request.user.is_coach:
            raise PermissionDenied("Area riservata ai Coach.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Scadenza 30gg: libera gli atleti scaduti prima di filtrare
        for athlete in self.request.user.athletes.all():
            athlete.refresh_subscription_status()
        # RBAC: il coach accede solo agli atleti a lui assegnati (no IDOR)
        return self.request.user.athletes.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workouts'] = WorkoutLog.objects.filter(user=self.object).order_by('-date')
        context.setdefault('goal_form', GoalForm())
        # Obiettivi correnti dell'atleta (per riferimento del coach)
        context['athlete_goals'] = Goal.objects.filter(user=self.object).order_by('-id')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()  # RBAC: deve essere un atleta del coach
        athlete = self.object

        # CASO A: il coach assegna un nuovo obiettivo all'atleta
        if request.POST.get('action') == 'create_goal':
            goal_form = GoalForm(request.POST)
            if goal_form.is_valid():
                goal = goal_form.save(commit=False)
                goal.user = athlete
                goal.assigned_by_coach = True  # 🧠 marcato come assegnato dal coach
                goal.save()
                return redirect('coach_athlete_detail', athlete_id=athlete.id)
            context = self.get_context_data(goal_form=goal_form)
            return self.render_to_response(context)

        # CASO B: salvataggio del feedback su un allenamento
        log = get_object_or_404(WorkoutLog, id=request.POST.get('log_id'), user=athlete)
        log.coach_feedback = request.POST.get('coach_feedback', '')
        log.save()
        return redirect('coach_athlete_detail', athlete_id=athlete.id)
