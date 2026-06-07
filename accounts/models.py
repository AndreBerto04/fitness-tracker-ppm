# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Ruoli e Relazioni
    is_coach = models.BooleanField(default=False)
    coach = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='athletes'
    )
    
    # Dati Antropometrici e Personali
    age = models.PositiveIntegerField(null=True, blank=True)
    weight = models.FloatField(verbose_name="Peso Corporeo (kg)", null=True, blank=True)
    body_fat = models.FloatField(verbose_name="Massa Grassa (%)", null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({'Coach' if self.is_coach else 'Atleta'})"

    # Helper metod per calcolare i suggerimenti in base al peso (Valutazione Multimediale UX)
    def get_suggested_goals(self):
        if not self.weight or self.is_coach:
            return []
        
        # Standard atletici basati su moltiplicatori del peso corporeo (BW)
        return [
            {
                'name': 'Target Panca Piana (Livello Intermedio)',
                'activity_type': 'FORZA',
                'exercise_name': 'Panca Piana',
                'target_value': round(self.weight * 1.0, 1),
                'unit': 'kg',
                'description': 'Sollevare il 100% del proprio peso corporeo per 1 rep massimale.'
            },
            {
                'name': 'Target Squat (Livello Intermedio)',
                'activity_type': 'FORZA',
                'exercise_name': 'Squat',
                'target_value': round(self.weight * 1.25, 1),
                'unit': 'kg',
                'description': 'Sollevare 1.25 volte il proprio peso corporeo per 1 rep massimale.'
            }
        ]