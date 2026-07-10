from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


# Home come CBV protetta dal LoginRequiredMixin (convenzione slide per le CBV)
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'


urlpatterns = [
    # Rotta per il pannello di amministrazione
    path('admin/', admin.site.urls),

    # Rotte custom dell'app accounts (login con form stilizzato + signup)
    path('accounts/', include('accounts.urls')),

    # URL nativi di Django per logout, password reset, ecc.
    path('accounts/', include('django.contrib.auth.urls')),

    # Pagina iniziale (Home) accessibile solo dopo il login
    path('', HomeView.as_view(), name='home'),

    # Rotte dell'app workouts (allenamenti, esercizi, serie, obiettivi, area coach)
    path('', include('workouts.urls')),
]
