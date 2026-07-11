from django.db import models
from django.conf import settings

class WorkoutLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workouts'
    )
    date = models.DateField(auto_now_add=True)
    title = models.CharField(max_length=100)
    coach_feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Allenamento di {self.user.username} il {self.date} - {self.title}"


class ExerciseSession(models.Model):
    ACTIVITY_CHOICES = [
        ('FORZA', 'Forza / Palestra / Corpo Libero'),
        ('CARDIO', 'Cardio / Corsa / Bici / Nuoto'),
    ]

    # ogni keyword porta a un solo muscolo; quelle piu specifiche vengono prima
    # delle generiche perche get_target_muscle() prende il primo match trovato
    MUSCLE_MAP = {
        'panca': 'Petto',
        'bench': 'Petto',
        'croci': 'Petto',
        'fly': 'Petto',
        'spinte': 'Petto',
        'dip': 'Petto',
        'piegamenti': 'Petto',
        'push up': 'Petto',
        'chest': 'Petto',
        'squat': 'Gambe',
        'leg': 'Gambe',
        'affondi': 'Gambe',
        'pressa': 'Gambe',
        'stacco': 'Gambe',
        'deadlift': 'Gambe',
        'quad': 'Gambe',
        'hamstring': 'Gambe',
        'glute': 'Gambe',
        'polpacci': 'Gambe',
        'calf': 'Gambe',
        'triceps': 'Tricipiti',
        'pushdown': 'Tricipiti',
        'french press': 'Tricipiti',
        'curl': 'Bicipiti',
        'biceps': 'Bicipiti',
        'arm': 'Bicipiti',
        'military': 'Spalle',
        'lento': 'Spalle',
        'shoulder press': 'Spalle',
        'lateral': 'Spalle',
        'deltoid': 'Spalle',
        'alzate': 'Spalle',
        'spalle': 'Spalle',
        'press': 'Spalle',
        'trazioni': 'Schiena',
        'pull up': 'Schiena',
        'lat machine': 'Schiena',
        'rematore': 'Schiena',
        'pulley': 'Schiena',
        'row': 'Schiena',
        'pull': 'Schiena',
        'lat': 'Schiena',
        'back': 'Schiena',
        'crunch': 'Addome',
        'plank': 'Addome',
        'core': 'Addome',
        'abs': 'Addome',
        'situp': 'Addome',
    }

    workout_log = models.ForeignKey(
        WorkoutLog,
        on_delete=models.CASCADE,
        related_name='exercises'
    )
    name = models.CharField(max_length=100)
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_CHOICES, default='FORZA')

    def __str__(self):
        return f"{self.name} ({self.get_activity_type_display()})"

    def get_target_muscle(self):
        if self.activity_type == 'CARDIO':
            return 'Sistema Cardiovascolare'
        name_lower = self.name.lower()
        for keyword, muscle in self.MUSCLE_MAP.items():
            if keyword in name_lower:
                return muscle
        return 'Generico / Altro'


class ExerciseSet(models.Model):
    exercise_session = models.ForeignKey(
        ExerciseSession,
        on_delete=models.CASCADE,
        related_name='sets'
    )
    reps = models.IntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    distance = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    rpe = models.IntegerField(blank=True, null=True)

    def __str__(self):
        if self.exercise_session.activity_type == 'FORZA':
            return f"Serie: {self.reps} rep @ {self.weight}kg - RPE {self.rpe}"
        return f"Frazione: {self.distance}km in {self.duration}min - RPE {self.rpe}"


class Goal(models.Model):
    ACTIVITY_CHOICES = [
        ('FORZA', 'Forza / Palestra / Corpo Libero'),
        ('CARDIO', 'Cardio / Corsa / Bici / Nuoto'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=100)
    target_value = models.CharField(max_length=100)
    is_completed = models.BooleanField(default=False)
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_CHOICES, default='FORZA')
    exercise_name = models.CharField(max_length=100, verbose_name="Nome Esercizio per calcolo", help_text="Es. Panca Piana o Corsa", default="Panca Piana")
    assigned_by_coach = models.BooleanField(default=False)

    def __str__(self):
        return f"Obiettivo di {self.user.username}: {self.title}"

    def get_progress(self):
        from workouts.models import ExerciseSet

        user_sets = ExerciseSet.objects.filter(
            exercise_session__workout_log__user=self.user,
            exercise_session__name__iexact=self.exercise_name
        )

        if not user_sets.exists():
            return 0

        try:
            target_num = float(self.target_value.replace('kg', '').replace('km', '').strip())
        except ValueError:
            return 0

        if self.activity_type == 'FORZA':
            current_max = max([float(s.weight) for s in user_sets if s.weight] or [0.0])
        else:
            current_max = max([float(s.distance) for s in user_sets if s.distance] or [0.0])

        if current_max >= target_num:
            if not self.is_completed:
                self.is_completed = True
                self.save()
            return 100

        return int((current_max / target_num) * 100)
