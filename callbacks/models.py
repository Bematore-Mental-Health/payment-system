from django.db import models
from django.utils import timezone


class CallbackLog(models.Model):
    """
    Log of all payment callbacks received from payment providers
    """
    PROVIDER_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('flutterwave', 'Flutterwave'),
    ]
    
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    transaction_id = models.CharField(max_length=255)
    raw_data = models.JSONField()
    success = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'callback_logs'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.provider} - {self.transaction_id} ({self.created_at})"
