from django.db import models
from django.utils import timezone


class SyncLog(models.Model):
    """
    Track synchronization activities between Django and Firebase
    """
    SYNC_TYPES = [
        ('payment', 'Payment Data'),
        ('user', 'User Data'),
        ('status', 'Status Update'),
    ]
    
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    transaction_id = models.CharField(max_length=255, blank=True)
    user_uid = models.CharField(max_length=128, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    data_synced = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'firebase_sync_logs'
        ordering = ['-created_at']
        
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.sync_type} sync - {status} ({self.created_at})"
