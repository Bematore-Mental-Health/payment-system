"""
Bematore Payment System - Home Views
Professional Payment Processing Platform
Developed by Brandon Ochieng | Bematore Technologies
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.conf import settings
from .version import get_version_info, PLATFORM_NAME, DEVELOPER, ORGANIZATION


class HomeView(TemplateView):
    """
    Enterprise home page view for Bematore Payment System
    """
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        version_info = get_version_info()
        
        context.update({
            'title': PLATFORM_NAME,
            'description': 'Professional Payment Processing Platform for Bematore Technologies',
            'version': version_info['version'],
            'developer': DEVELOPER,
            'company': ORGANIZATION,
            'debug': settings.DEBUG,
            'platform_info': settings.PLATFORM_INFO if hasattr(settings, 'PLATFORM_INFO') else {},
        })
        return context


def home_api(request):
    """
    Enterprise API endpoint for system information
    """
    version_info = get_version_info()
    
    return JsonResponse({
        'service': PLATFORM_NAME,
        'version': version_info['version'],
        'build': version_info['build_number'],
        'release': version_info['release_name'],
        'status': 'operational',
        'developer': DEVELOPER,
        'organization': ORGANIZATION,
        'description': 'Professional Payment Processing Platform for Bematore Technologies',
        'features': {
            'mpesa_integration': True,
            'firebase_sync': True,
            'enterprise_security': True,
            'comprehensive_logging': True,
        },
        'endpoints': {
            'payments': '/payments/',
            'admin': f'/{settings.ADMIN_URL if hasattr(settings, "ADMIN_URL") else "admin/"}',
            'health': '/health/',
            'callbacks': '/callbacks/',
        }
    })