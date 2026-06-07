from django.contrib import admin
from .models import WorkoutLog, ExerciseSession, ExerciseSet, Goal

admin.site.register(WorkoutLog)
admin.site.register(ExerciseSession)
admin.site.register(ExerciseSet)
admin.site.register(Goal)

