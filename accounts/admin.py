from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Mostra i campi personalizzati nel pannello di modifica
    fieldsets = UserAdmin.fieldsets + (
        ('Informazioni Coach', {'fields': ('is_coach', 'coach', 'age')}),
    )
    # Mostra i campi personalizzati durante la creazione guidata
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informazioni Coach', {'fields': ('is_coach', 'coach', 'age')}),
    )

# Registra il modello CustomUser
admin.site.register(CustomUser, CustomUserAdmin)