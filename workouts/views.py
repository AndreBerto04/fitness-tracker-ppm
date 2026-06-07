from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from .models import WorkoutLog, ExerciseSession, ExerciseSet, Goal  # 🆕 Aggiunto Goal agli import
from .forms import WorkoutLogForm

# 1. LISTA STORICO (Read) - con biforcazione RBAC Coach/Atleta
@login_required
def workout_list(request):
    # RBAC: il Coach non vede i propri log ma la dashboard dei suoi atleti
    if request.user.is_coach:
        athletes = request.user.athletes.all()
        return render(request, 'workouts/coach_dashboard.html', {'athletes': athletes})

    workouts = WorkoutLog.objects.filter(user=request.user).order_by('-date')
    return render(request, 'workouts/workout_list.html', {'workouts': workouts})

# 2. CREAZIONE NUOVO ALLENAMENTO (Create - Passo 1)
@login_required
def workout_create(request):
    if request.method == 'POST':
        form = WorkoutLogForm(request.POST)
        if form.is_valid():
            workout = form.save(commit=False)
            workout.user = request.user
            workout.save()
            return redirect('workout_detail', pk=workout.pk)
    else:
        form = WorkoutLogForm()
    return render(request, 'workouts/workout_form.html', {'form': form})

# 3. DETTAGLIO HUB E AGGIUNTA SERIE (Create - Passo 2)
@login_required
def workout_detail(request, pk):
    workout = get_object_or_404(WorkoutLog, pk=pk, user=request.user)
    
    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        
        # CASO 1: L'UTENTE CREA SOLO IL NOME DELL'ESERCIZIO
        if action_type == 'create_exercise':
            exercise_name = request.POST.get('exercise_name')
            activity_type = request.POST.get('activity_type')
            if exercise_name:
                ExerciseSession.objects.create(
                    workout_log=workout,
                    name=exercise_name,
                    activity_type=activity_type
                )
        
        # CASO 2: L'UTENTE AGGIUNGE UNA SERIE A UN ESERCIZIO ESISTENTE
        elif action_type == 'add_set':
            exercise_id = request.POST.get('exercise_id')
            exercise = get_object_or_404(ExerciseSession, id=exercise_id, workout_log=workout)
            rpe = request.POST.get('rpe')
            
            if exercise.activity_type == 'FORZA':
                reps = request.POST.get('reps')
                weight = request.POST.get('weight')
                ExerciseSet.objects.create(
                    exercise_session=exercise,
                    reps=reps if reps else None,
                    weight=weight if weight else None,
                    rpe=rpe if rpe else None
                )
            elif exercise.activity_type == 'CARDIO':
                distance = request.POST.get('distance')
                duration = request.POST.get('duration')
                ExerciseSet.objects.create(
                    exercise_session=exercise,
                    distance=distance if distance else None,
                    duration=duration if duration else None,
                    rpe=rpe if rpe else None
                )
                
        return redirect('workout_detail', pk=workout.pk)

    return render(request, 'workouts/workout_detail.html', {'workout': workout})

# 4. MODIFICA TITOLO ALLENAMENTO (Update)
@login_required
def workout_update(request, pk):
    workout = get_object_or_404(WorkoutLog, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = WorkoutLogForm(request.POST, instance=workout)
        if form.is_valid():
            form.save()
            
            # Intercettiamo quale pulsante è stato premuto nel form
            save_mode = request.POST.get('save_mode')
            
            if save_mode == 'quick_save':
                return redirect('workout_list')
            else:
                return redirect('workout_detail', pk=workout.pk)
    else:
        form = WorkoutLogForm(instance=workout)
        
    return render(request, 'workouts/workout_form.html', {'form': form, 'is_update': True})

# 5. CANCELLAZIONE ALLENAMENTO (Delete)
@login_required
def workout_delete(request, pk):
    workout = get_object_or_404(WorkoutLog, pk=pk, user=request.user)
    if request.method == 'POST':
        workout.delete()
        return redirect('workout_list')
    return render(request, 'workouts/workout_confirm_delete.html', {'workout': workout})

# 6. VISTA PER ELIMINARE UN INTERO ESERCIZIO (E LE SUE SERIE)
@login_required
def delete_exercise(request, pk):
    exercise = get_object_or_404(ExerciseSession, pk=pk, workout_log__user=request.user)
    workout_pk = exercise.workout_log.pk
    exercise.delete()
    return redirect('workout_detail', pk=workout_pk)

# 7. VISTA PER ELIMINARE UNA SINGOLA SERIE
@login_required
def delete_set(request, pk):
    set_obj = get_object_or_404(ExerciseSet, pk=pk, exercise_session__workout_log__user=request.user)
    workout_pk = set_obj.exercise_session.workout_log.pk
    set_obj.delete()
    return redirect('workout_detail', pk=workout_pk)

# 🆕 8. GESTIONE E DASHBOARD OBIETTIVI (Read & Create Obiettivi Suggeriti)
@login_required
def goal_list(request):
    # Gestione della richiesta POST: l'utente ha cliccato su "Attiva" per un obiettivo suggerito
    if request.method == 'POST':
        title = request.POST.get('title')
        target_value = request.POST.get('target_value')
        exercise_name = request.POST.get('exercise_name')
        activity_type = request.POST.get('activity_type')
        
        if title and target_value:
            Goal.objects.create(
                user=request.user,
                title=title,
                target_value=target_value,
                exercise_name=exercise_name if exercise_name else "Panca Piana",
                activity_type=activity_type if activity_type else "FORZA"
            )
        return redirect('goal_list')

    # Gestione della richiesta GET: estraiamo gli obiettivi correnti dell'atleta
    goals = Goal.objects.filter(user=request.user).order_by('-id')
    
    # Calcoliamo dinamicamente i suggerimenti in base al peso corporeo (se inserito nel profilo)
    suggested_goals = []
    if hasattr(request.user, 'get_suggested_goals'):
        suggested_goals = request.user.get_suggested_goals()

    context = {
        'goals': goals,
        'suggested_goals': suggested_goals,
    }
    return render(request, 'workouts/goal_list.html', context)

# 🆕 9. DETTAGLIO ATLETA PER IL COACH (Read log + Update coach_feedback)
@login_required
def coach_athlete_detail(request, athlete_id):
    # RBAC: solo un coach può accedere e solo a un atleta a lui assegnato
    if not request.user.is_coach:
        raise Http404("Accesso riservato ai coach.")
    athlete = get_object_or_404(request.user.athletes, id=athlete_id)

    # Update rapido: salvataggio del feedback su un singolo WorkoutLog
    if request.method == 'POST':
        log = get_object_or_404(WorkoutLog, id=request.POST.get('log_id'), user=athlete)
        log.coach_feedback = request.POST.get('coach_feedback', '')
        log.save()
        return redirect('coach_athlete_detail', athlete_id=athlete.id)

    workouts = WorkoutLog.objects.filter(user=athlete).order_by('-date')
    return render(request, 'workouts/coach_athlete_detail.html', {
        'athlete': athlete,
        'workouts': workouts,
    })