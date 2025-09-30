"""
Callback URLs
"""

from django.urls import path
from . import views

urlpatterns = [
    # M-Pesa callbacks
    path('mpesa/', views.MpesaCallbackView.as_view(), name='mpesa_callback'),
    path('mpesa/result/', views.mpesa_result_callback, name='mpesa_result_callback'),
    
    # Flutterwave webhooks
    path('flutterwave/', views.FlutterwaveWebhookView.as_view(), name='flutterwave_webhook'),
]