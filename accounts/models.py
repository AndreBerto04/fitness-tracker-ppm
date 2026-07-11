from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_coach = models.BooleanField(default=False)
    coach = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='athletes'
    )

    age = models.PositiveIntegerField(null=True, blank=True)
    weight = models.FloatField(verbose_name="Peso Corporeo (kg)", null=True, blank=True)
    body_fat = models.FloatField(verbose_name="Massa Grassa (%)", null=True, blank=True)

    prezzo_mensile = models.DecimalField(
        verbose_name="Prezzo mensile (€)",
        max_digits=6, decimal_places=2, default=0.00
    )

    def __str__(self):
        return f"{self.username} ({'Coach' if self.is_coach else 'Atleta'})"

    def get_active_subscription(self):
        """Per l'atleta: la richiesta ACCEPTED verso il coach attualmente associato."""
        if self.is_coach or not self.coach_id:
            return None
        return self.sent_requests.filter(
            coach=self.coach, status='ACCEPTED'
        ).order_by('-data_richiesta').first()

    def refresh_subscription_status(self):
        """Libera l'atleta se l'abbonamento al coach è scaduto (oltre 30 giorni)."""
        from django.utils import timezone
        if self.is_coach or not self.coach_id:
            return
        sub = self.get_active_subscription()
        if sub and sub.data_scadenza and sub.data_scadenza < timezone.now().date():
            sub.status = 'EXPIRED'
            sub.save()
            self.coach = None
            self.save()

    def get_suggested_goals(self):
        if not self.weight or self.is_coach:
            return []

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


class SubscriptionRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'In attesa'),
        ('ACCEPTED', 'Accettata'),
        ('REJECTED', 'Rifiutata'),
        ('CANCELLED', 'Annullata'),
        ('EXPIRED', 'Scaduta'),
    ]

    atleta = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests'
    )
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_requests'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    data_richiesta = models.DateTimeField(auto_now_add=True)
    data_scadenza = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-data_richiesta']

    def __str__(self):
        return f"{self.atleta.username} -> {self.coach.username} [{self.status}]"