"""
Firebase Authentication Middleware

Middleware to handle Firebase authentication for web views and
provide user context throughout the payment process.
"""

import logging
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from .authentication import FirebaseAuthentication

logger = logging.getLogger(__name__)


class FirebaseAuthenticationMiddleware:
    """
    Middleware to authenticate users via Firebase tokens for web views
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.firebase_auth = FirebaseAuthentication()
        
        # URLs that don't require authentication
        self.exempt_urls = [
            '/api/v1/callbacks/',  # Payment callbacks
            '/health/',           # Health check
            '/admin/',           # Django admin
        ]
    
    def __call__(self, request):
        # Skip authentication for exempt URLs
        if any(request.path.startswith(url) for url in self.exempt_urls):
            response = self.get_response(request)
            return response
            
        # Try to authenticate via Firebase for web views
        if not request.path.startswith('/api/'):  # Web views only
            firebase_token = request.GET.get('token') or request.session.get('firebase_token')
            
            if firebase_token:
                request.META['HTTP_FIREBASE_TOKEN'] = firebase_token
                try:
                    auth_result = self.firebase_auth.authenticate(request)
                    if auth_result:
                        request.user = auth_result[0]
                        request.session['firebase_token'] = firebase_token
                        request.session['user_uid'] = auth_result[0].uid
                except Exception as e:
                    logger.warning(f"Firebase authentication failed in middleware: {e}")
                    request.user = None
            
            # Redirect to error page if authentication is required but failed
            if not hasattr(request, 'user') or not request.user:
                if request.path.startswith('/payment/'):
                    return JsonResponse({
                        'error': 'Authentication required',
                        'redirect_url': 'https://app.bematore.com/login'
                    }, status=401)
        
        response = self.get_response(request)
        return response