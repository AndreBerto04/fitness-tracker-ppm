from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from workouts.views import (
    workout_list, workout_create, workout_update, workout_delete, workout_detail,
    delete_exercise, delete_set, coach_athlete_detail, goal_list
)

urlpatterns = [
    # Rotta per il pannello di amministrazione 
    path('admin/', admin.site.urls),
    
    # Include tutti gli URL nativi di Django per login e logout
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Pagina iniziale temporanea (Home) accessibile solo dopo il login
    path('', login_required(TemplateView.as_view(template_name='home.html')), name='home'),

    # Rotta per visualizzare la lista degli allenamenti
    path('workouts/', workout_list, name='workout_list'),

    # Nuova rotta per la creazione degli allenamenti!
    path('workouts/nuovo/', workout_create, name='workout_create'),
    
    # Rotte per l'aggiornamento e l'eliminazione degli allenamenti
    path('workouts/<int:pk>/modifica/', workout_update, name='workout_update'),
    path('workouts/<int:pk>/elimina/', workout_delete, name='workout_delete'),
    path('workouts/<int:pk>/', workout_detail, name='workout_detail'),

    # Rotte per l'eliminazione di esercizi e serie
    path('exercises/<int:pk>/elimina/', delete_exercise, name='delete_exercise'),
    path('sets/<int:pk>/elimina/', delete_set, name='delete_set'),

    # 🆕 Rotta RBAC: dettaglio atleta lato Coach
    path('coach/atleta/<int:athlete_id>/', coach_athlete_detail, name='coach_athlete_detail'),

    # 🆕 Rotta per la gestione degli obiettivi
    path('obiettivi/', goal_list, name='goal_list'),
]
