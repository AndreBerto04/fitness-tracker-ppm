from django import forms
from .models import WorkoutLog, ExerciseSession, ExerciseSet, Goal


class WorkoutLogForm(forms.ModelForm):
    class Meta:
        model = WorkoutLog

        fields = ['title']

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Es. Allenamento Spinta, Corsa Mattutina...'
            }),
        }


# ModelForm per la creazione di un esercizio (Passo 1 del dettaglio)
class ExerciseSessionForm(forms.ModelForm):
    class Meta:
        model = ExerciseSession
        fields = ['name', 'activity_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Es. Panca Piana, Squat, Corsa...'
            }),
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
        }


# ModelForm per l'inserimento di una serie/frazione (Passo 2 del dettaglio)
class ExerciseSetForm(forms.ModelForm):
    class Meta:
        model = ExerciseSet
        fields = ['reps', 'weight', 'distance', 'duration', 'rpe']
        widgets = {
            'reps': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Es. 10'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Es. 50'}),
            'distance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Es. 5.0'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Es. 25'}),
            'rpe': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10, 'placeholder': 'Es. 8'}),
        }


# ModelForm per l'attivazione/creazione di un obiettivo
class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'target_value', 'exercise_name', 'activity_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'target_value': forms.TextInput(attrs={'class': 'form-control'}),
            'exercise_name': forms.TextInput(attrs={'class': 'form-control'}),
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
        }
