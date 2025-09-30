"""
Payment Models

Django models for caching payment data locally while Firebase
serves as the primary data store.
"""

from django.db import models
from django.utils import timezone
import uuid


class PaymentTransaction(models.Model):
    """
    Local cache model for payment transactions
    Primary data is stored in Firebase
    """
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('flutterwave', 'Flutterwave'),
        ('paypal', 'PayPal'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PURPOSES = [
        ('assessment', 'Assessment Payment'),
        ('subscription', 'Subscription Payment'),
        ('consultation', 'Consultation Payment'),
    ]
    
    # Primary identifiers
    transaction_id = models.CharField(max_length=100, unique=True, primary_key=True)
    user_uid = models.CharField(max_length=100, db_index=True)
    
    # User information
    email = models.EmailField()
    name = models.CharField(max_length=200, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    purpose = models.CharField(max_length=20, choices=PURPOSES, default='assessment')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Provider-specific data
    mpesa_checkout_request_id = models.CharField(max_length=100, blank=True)
    mpesa_receipt = models.CharField(max_length=50, blank=True)
    flutterwave_tx_ref = models.CharField(max_length=100, blank=True)
    flutterwave_flw_ref = models.CharField(max_length=100, blank=True)
    paypal_payment_id = models.CharField(max_length=100, blank=True)
    
    # Error handling
    failure_reason = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Metadata for currency conversion tracking
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_uid', 'status']),
            models.Index(fields=['payment_method', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.email} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = str(uuid.uuid4())
        
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    @property
    def is_successful(self):
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        return self.status in ['pending', 'processing']
    
    @property
    def can_retry(self):
        return self.status == 'failed' and self.retry_count < 3
