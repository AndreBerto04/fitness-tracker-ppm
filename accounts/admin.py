from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, SubscriptionRequest

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Mostra i campi personalizzati nel pannello di modifica
    fieldsets = UserAdmin.fieldsets + (
        ('Informazioni Coach', {'fields': ('is_coach', 'coach', 'age', 'prezzo_mensile')}),
    )
    # Mostra i campi personalizzati durante la creazione guidata
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informazioni Coach', {'fields': ('is_coach', 'coach', 'age', 'prezzo_mensile')}),
    )

@admin.register(SubscriptionRequest)
class SubscriptionRequestAdmin(admin.ModelAdmin):
    list_display = ('atleta', 'coach', 'status', 'data_richiesta')
    list_filter = ('status',)

# Registra il modello CustomUser
admin.site.register(CustomUser, CustomUserAdmin)
