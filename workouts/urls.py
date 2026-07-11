from django.urls import path
from .views import (
    WorkoutListView, WorkoutCreateView, WorkoutUpdateView, WorkoutDeleteView,
    WorkoutDetailView, WorkoutEditView, ExerciseDeleteView, SetDeleteView,
    CoachAthleteDetailView, GoalListView, GoalDeleteView, GoalCompleteView,
)

urlpatterns = [
    path('workouts/', WorkoutListView.as_view(), name='workout_list'),
    path('workouts/nuovo/', WorkoutCreateView.as_view(), name='workout_create'),
    path('workouts/<int:pk>/modifica/', WorkoutUpdateView.as_view(), name='workout_update'),
    path('workouts/<int:pk>/gestisci/', WorkoutEditView.as_view(), name='workout_edit'),
    path('workouts/<int:pk>/elimina/', WorkoutDeleteView.as_view(), name='workout_delete'),
    path('workouts/<int:pk>/', WorkoutDetailView.as_view(), name='workout_detail'),

    path('exercises/<int:pk>/elimina/', ExerciseDeleteView.as_view(), name='delete_exercise'),
    path('sets/<int:pk>/elimina/', SetDeleteView.as_view(), name='delete_set'),

    path('coach/atleta/<int:athlete_id>/', CoachAthleteDetailView.as_view(), name='coach_athlete_detail'),

    path('obiettivi/', GoalListView.as_view(), name='goal_list'),
    path('obiettivi/<int:pk>/elimina/', GoalDeleteView.as_view(), name='goal_delete'),
    path('obiettivi/<int:pk>/completa/', GoalCompleteView.as_view(), name='goal_complete'),
]
