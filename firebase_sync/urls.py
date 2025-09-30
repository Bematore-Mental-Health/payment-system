"""
Firebase Sync URLs
"""

from django.urls import path
from . import views

urlpatterns = [
    # Sync payment status to Firebase
    path('sync-payment/<str:transaction_id>/', views.SyncPaymentView.as_view(), name='sync_payment'),
    
    # Get user data from Firebase
    path('user-data/<str:uid>/', views.UserDataView.as_view(), name='user_data'),
]