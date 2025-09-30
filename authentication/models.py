from django.db import models
from django.utils import timezone


class FirebaseUser(models.Model):
    """
    Local cache of Firebase user data for faster lookups
    """
    uid = models.CharField(max_length=128, unique=True, primary_key=True)
    email = models.EmailField()
    display_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_firebase_users'
        
    def __str__(self):
        return f"{self.email} ({self.uid})"
