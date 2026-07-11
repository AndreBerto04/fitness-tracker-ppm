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


class WorkoutListView(LoginRequiredMixin, ListView):
    model = WorkoutLog
    template_name = 'workouts/workout_list.html'
    context_object_name = 'workouts'

    def get(self, request, *args, **kwargs):
        if request.user.is_coach:
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
        return WorkoutLog.objects.filter(user=self.request.user).order_by('-date')


class WorkoutCreateView(LoginRequiredMixin, CreateView):
    model = WorkoutLog
    form_class = WorkoutLogForm
    template_name = 'workouts/workout_form.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('workout_edit', kwargs={'pk': self.object.pk})


class WorkoutDetailView(LoginRequiredMixin, DetailView):
    model = WorkoutLog
    template_name = 'workouts/workout_detail.html'
    context_object_name = 'workout'

    def get_queryset(self):
        # proprietario del log o il suo coach, mai altri utenti
        return WorkoutLog.objects.filter(
            Q(user=self.request.user) | Q(user__coach=self.request.user)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workout = self.object

        total_volume = 0.0
        muscle_sets = {}

        for exercise in workout.exercises.all():
            sets = list(exercise.sets.all())
            n_sets = len(sets)

            muscle = exercise.get_target_muscle()
            muscle_sets[muscle] = muscle_sets.get(muscle, 0) + n_sets

            for s in sets:
                if s.reps and s.weight:
                    total_volume += s.reps * float(s.weight)

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


class WorkoutEditView(LoginRequiredMixin, DetailView):
    model = WorkoutLog
    template_name = 'workouts/workout_edit.html'
    context_object_name = 'workout'

    def get_queryset(self):
        return WorkoutLog.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        workout = self.object
        action_type = request.POST.get('action_type')

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


class WorkoutUpdateView(LoginRequiredMixin, UpdateView):
    model = WorkoutLog
    form_class = WorkoutLogForm
    template_name = 'workouts/workout_form.html'

    def get_queryset(self):
        return WorkoutLog.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def get_success_url(self):
        if self.request.POST.get('save_mode') == 'quick_save':
            return reverse('workout_list')
        return reverse('workout_edit', kwargs={'pk': self.object.pk})


class WorkoutDeleteView(LoginRequiredMixin, DeleteView):
    model = WorkoutLog
    template_name = 'workouts/workout_confirm_delete.html'
    context_object_name = 'workout'
    success_url = reverse_lazy('workout_list')

    def get_queryset(self):
        return WorkoutLog.objects.filter(user=self.request.user)


class ExerciseDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        exercise = get_object_or_404(ExerciseSession, pk=pk, workout_log__user=request.user)
        workout_pk = exercise.workout_log.pk
        exercise.delete()
        return redirect('workout_edit', pk=workout_pk)


class SetDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        set_obj = get_object_or_404(ExerciseSet, pk=pk, exercise_session__workout_log__user=request.user)
        workout_pk = set_obj.exercise_session.workout_log.pk
        set_obj.delete()
        return redirect('workout_edit', pk=workout_pk)


class GoalListView(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'workouts/goal_list.html'
    context_object_name = 'goals'

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'get_suggested_goals'):
            context['suggested_goals'] = self.request.user.get_suggested_goals()
        else:
            context['suggested_goals'] = []
        context.setdefault('goal_form', GoalForm())
        context.setdefault('profile_form', ProfileForm(instance=self.request.user))
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        self.object_list = self.get_queryset()

        if action == 'update_profile':
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                return redirect('goal_list')
            context = self.get_context_data(profile_form=profile_form)
            return self.render_to_response(context)

        goal_form = GoalForm(request.POST)
        if goal_form.is_valid():
            goal = goal_form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('goal_list')
        context = self.get_context_data(goal_form=goal_form)
        return self.render_to_response(context)


class GoalDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        goal = get_object_or_404(Goal, pk=pk, user=request.user)
        goal.delete()
        return redirect('goal_list')


class GoalCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        goal = get_object_or_404(Goal, pk=pk, user=request.user)
        goal.is_completed = not goal.is_completed
        goal.save()
        return redirect('goal_list')


class CoachAthleteDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'workouts/coach_athlete_detail.html'
    context_object_name = 'athlete'
    pk_url_kwarg = 'athlete_id'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_coach:
            raise PermissionDenied("Area riservata ai Coach.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        for athlete in self.request.user.athletes.all():
            athlete.refresh_subscription_status()
        return self.request.user.athletes.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workouts'] = WorkoutLog.objects.filter(user=self.object).order_by('-date')
        context.setdefault('goal_form', GoalForm())
        context['athlete_goals'] = Goal.objects.filter(user=self.object).order_by('-id')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        athlete = self.object

        if request.POST.get('action') == 'create_goal':
            goal_form = GoalForm(request.POST)
            if goal_form.is_valid():
                goal = goal_form.save(commit=False)
                goal.user = athlete
                goal.assigned_by_coach = True
                goal.save()
                return redirect('coach_athlete_detail', athlete_id=athlete.id)
            context = self.get_context_data(goal_form=goal_form)
            return self.render_to_response(context)

        log = get_object_or_404(WorkoutLog, id=request.POST.get('log_id'), user=athlete)
        log.coach_feedback = request.POST.get('coach_feedback', '')
        log.save()
        return redirect('coach_athlete_detail', athlete_id=athlete.id)
