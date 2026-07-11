from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, SubscriptionRequest

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        ('Informazioni Coach', {'fields': ('is_coach', 'coach', 'age', 'prezzo_mensile')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informazioni Coach', {'fields': ('is_coach', 'coach', 'age', 'prezzo_mensile')}),
    )

@admin.register(SubscriptionRequest)
class SubscriptionRequestAdmin(admin.ModelAdmin):
    list_display = ('atleta', 'coach', 'status', 'data_richiesta')
    list_filter = ('status',)

admin.site.register(CustomUser, CustomUserAdmin)
