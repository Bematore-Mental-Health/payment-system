"""
Authentication URLs
"""

from django.urls import path
from . import views

urlpatterns = [
    # Firebase token verification
    path('verify-token/', views.VerifyTokenView.as_view(), name='verify_token'),
    
    # User profile
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
]