from django.urls import path
from .views import (
    WorkoutListView, WorkoutCreateView, WorkoutUpdateView, WorkoutDeleteView,
    WorkoutDetailView, WorkoutEditView, ExerciseDeleteView, SetDeleteView,
    CoachAthleteDetailView, GoalListView, GoalDeleteView, GoalCompleteView,
)

urlpatterns = [
    # Rotta per visualizzare la lista degli allenamenti
    path('workouts/', WorkoutListView.as_view(), name='workout_list'),

    # Nuova rotta per la creazione degli allenamenti!
    path('workouts/nuovo/', WorkoutCreateView.as_view(), name='workout_create'),

    # Rotte per l'aggiornamento e l'eliminazione degli allenamenti
    path('workouts/<int:pk>/modifica/', WorkoutUpdateView.as_view(), name='workout_update'),
    path('workouts/<int:pk>/gestisci/', WorkoutEditView.as_view(), name='workout_edit'),
    path('workouts/<int:pk>/elimina/', WorkoutDeleteView.as_view(), name='workout_delete'),
    path('workouts/<int:pk>/', WorkoutDetailView.as_view(), name='workout_detail'),

    # Rotte per l'eliminazione di esercizi e serie
    path('exercises/<int:pk>/elimina/', ExerciseDeleteView.as_view(), name='delete_exercise'),
    path('sets/<int:pk>/elimina/', SetDeleteView.as_view(), name='delete_set'),

    # Rotta RBAC: dettaglio atleta lato Coach
    path('coach/atleta/<int:athlete_id>/', CoachAthleteDetailView.as_view(), name='coach_athlete_detail'),

    # Rotta per la gestione degli obiettivi
    path('obiettivi/', GoalListView.as_view(), name='goal_list'),
    path('obiettivi/<int:pk>/elimina/', GoalDeleteView.as_view(), name='goal_delete'),
    path('obiettivi/<int:pk>/completa/', GoalCompleteView.as_view(), name='goal_complete'),
]
