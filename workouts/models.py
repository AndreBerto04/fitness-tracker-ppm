from django.db import models
from django.conf import settings

# 1. IL CONTENITORE GENERALE DELL'ALLENAMENTO
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


# 2. IL SINGOLO ESERCIZIO O ATTIVITÀ
class ExerciseSession(models.Model):
    ACTIVITY_CHOICES = [
        ('FORZA', 'Forza / Palestra / Corpo Libero'),
        ('CARDIO', 'Cardio / Corsa / Bici / Nuoto'),
    ]

    workout_log = models.ForeignKey(
        WorkoutLog, 
        on_delete=models.CASCADE, 
        related_name='exercises'
    )
    name = models.CharField(max_length=100)  # Es. "Panca Piana" o "Corsa"
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_CHOICES, default='FORZA')

    def __str__(self):
        return f"{self.name} ({self.get_activity_type_display()})"


# 3. LE SINGOLE SERIE O FRAZIONI DI ALLENAMENTO
class ExerciseSet(models.Model):
    exercise_session = models.ForeignKey(
        ExerciseSession, 
        on_delete=models.CASCADE, 
        related_name='sets'
    )
    reps = models.IntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True) # Corretto max_length rimosso (invalido su DecimalField)
    
    distance = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    rpe = models.IntegerField(blank=True, null=True)

    def __str__(self):
        if self.exercise_session.activity_type == 'FORZA':
            return f"Serie: {self.reps} rep @ {self.weight}kg - RPE {self.rpe}"
        return f"Frazione: {self.distance}km in {self.duration}min - RPE {self.rpe}"


# 4. GLI OBIETTIVI (Modificato con logica di tracciamento avanzata)
class Goal(models.Model):
    ACTIVITY_CHOICES = [
        ('FORZA', 'Forza / Palestra / Corpo Libero'),
        ('CARDIO', 'Cardio / Corsa / Bici / Nuoto'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=100)       # Es. "Spingere più di peso corporeo"
    target_value = models.CharField(max_length=100) # Es. "80" o "10" (mantenuto testo come tua versione)
    is_completed = models.BooleanField(default=False)
    
    # 🆕 Campi aggiunti per collegare l'obiettivo alla logica dei log d'allenamento
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_CHOICES, default='FORZA')
    exercise_name = models.CharField(max_length=100, verbose_name="Nome Esercizio per calcolo", help_text="Es. Panca Piana o Corsa", default="Panca Piana")

    def __str__(self):
        return f"Obiettivo di {self.user.username}: {self.title}"

    # 🧠 Algoritmo teorico-pratico per estrarre la percentuale di completamento
    def get_progress(self):
        # Evitiamo import circolari caricando il modello a runtime
        from workouts.models import ExerciseSet
        
        # 1. Recuperiamo tutte le serie dell'utente per questo specifico esercizio (Es. "Panca Piana")
        user_sets = ExerciseSet.objects.filter(
            exercise_session__workout_log__user=self.user,
            exercise_session__name__iexact=self.exercise_name
        )
        
        if not user_sets.exists():
            return 0
            
        # 2. Convertiamo il target_value da stringa a numero float per fare i calcoli matematici
        try:
            target_num = float(self.target_value.replace('kg', '').replace('km', '').strip())
        except ValueError:
            return 0 # Se la stringa non è convertibile, restituisce 0%
            
        # 3. Cerchiamo il picco massimo raggiunto nei log dell'atleta
        if self.activity_type == 'FORZA':
            current_max = max([float(s.weight) for s in user_sets if s.weight] or [0.0])
        else:
            current_max = max([float(s.distance) for s in user_sets if s.distance] or [0.0])
            
        # 4. Se il massimale corrente supera o uguaglia il target, l'obiettivo è conquistato!
        if current_max >= target_num:
            if not self.is_completed:
                self.is_completed = True
                self.save() # Aggiorna la colonna is_completed direttamente nel database
            return 100
            
        # Calcolo matematico della percentuale
        return int((current_max / target_num) * 100)