from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from accounts.models import CustomUser
from .models import WorkoutLog, ExerciseSession, ExerciseSet, Goal
from .forms import WorkoutLogForm, ExerciseSessionForm, ExerciseSetForm, GoalForm


# 1. LISTA STORICO (Read) - con biforcazione RBAC Coach/Atleta
class WorkoutListView(LoginRequiredMixin, ListView):
    model = WorkoutLog
    template_name = 'workouts/workout_list.html'
    context_object_name = 'workouts'

    def get(self, request, *args, **kwargs):
        # RBAC: il Coach vede la dashboard dei suoi atleti, non i propri log
        if request.user.is_coach:
            return render(request, 'workouts/coach_dashboard.html',
                          {'athletes': request.user.athletes.all()})
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
        # RBAC: l'atleta accede solo ai propri log
        return WorkoutLog.objects.filter(user=self.request.user)

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
class ExerciseDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        exercise = get_object_or_404(ExerciseSession, pk=pk, workout_log__user=request.user)
        workout_pk = exercise.workout_log.pk
        exercise.delete()
        return redirect('workout_edit', pk=workout_pk)


# 7. ELIMINA UNA SINGOLA SERIE
class SetDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
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
        return context

    def post(self, request, *args, **kwargs):
        # Creazione obiettivo tramite ModelForm (validazione nativa)
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('goal_list')
        # Form non valido: rirenderizza la lista mostrando gli errori
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        context['goal_form'] = form
        return self.render_to_response(context)


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
        # RBAC: il coach accede solo agli atleti a lui assegnati (no IDOR)
        return self.request.user.athletes.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workouts'] = WorkoutLog.objects.filter(user=self.object).order_by('-date')
        return context

    def post(self, request, *args, **kwargs):
        athlete = self.get_object()  # RBAC: deve essere un atleta del coach
        log = get_object_or_404(WorkoutLog, id=request.POST.get('log_id'), user=athlete)
        log.coach_feedback = request.POST.get('coach_feedback', '')
        log.save()
        return redirect('coach_athlete_detail', athlete_id=athlete.id)
