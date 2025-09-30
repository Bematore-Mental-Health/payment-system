"""
Home views for Bematore Payment System
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.conf import settings


class HomeView(TemplateView):
    """
    Home page view for Bematore Payment System
    """
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Bematore Payment System',
            'description': 'Professional payment processing for mental health services',
            'version': '1.0.0',
            'developer': 'Brandon Ochieng',
            'company': 'Bematore Mental Health Solutions',
            'debug': settings.DEBUG,
        })
        return context


def home_api(request):
    """
    API endpoint for home/system info
    """
    return JsonResponse({
        'service': 'Bematore Payment System',
        'version': '1.0.0',
        'status': 'operational',
        'developer': 'Brandon Ochieng',
        'company': 'Bematore Mental Health Solutions',
        'description': 'Professional payment processing platform for mental health services',
        'endpoints': {
            'payments': '/payments/',
            'admin': f'/{settings.ADMIN_URL if hasattr(settings, "ADMIN_URL") else "admin/"}',
            'health': '/health/',
            'api_docs': '/api/docs/',
        }
    })