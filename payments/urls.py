"""
Payment URLs
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Root payment URL (for Flutter app)
    path('', views.PaymentFormView.as_view(), name='payment_root'),
    
    # Web payment form views
    path('form/', views.PaymentFormView.as_view(), name='payment_form'),
    path('status/<str:transaction_id>/', views.PaymentStatusView.as_view(), name='payment_status'),
    
    # API endpoints for payment initiation and status
    path('api/initiate/', views.PaymentInitiationView.as_view(), name='payment_initiate'),
    path('api/status/<str:transaction_id>/', views.PaymentStatusAPIView.as_view(), name='payment_status_api'),
    
    # Payment callbacks (redirects from payment providers)
    path('callback/<str:provider>/<str:transaction_id>/', views.PaymentCallbackView.as_view(), name='payment_callback'),
]