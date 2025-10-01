"""
Bematore Payment System - Main URL Configuration
Professional Payment Processing Platform
Developed by Brandon Ochieng | Bematore Technologies
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .views import HomeView, home_api
from .version import get_version_info

# Custom error handlers
handler404 = 'bematore_payments.error_views.handler404'
handler500 = 'bematore_payments.error_views.handler500'
handler403 = 'bematore_payments.error_views.handler403'
handler400 = 'bematore_payments.error_views.handler400'

@csrf_exempt
def health_check(request):
    """Enterprise health check endpoint with comprehensive system information."""
    version_info = get_version_info()
    return JsonResponse({
        'status': 'healthy',
        'service': 'bematore-payment-system',
        'platform': 'Professional Payment Processing Platform',
        'developer': version_info['author'],
        'organization': version_info['organization'],
        'version': version_info['version'],
        'build': version_info['build_number'],
        'release': version_info['release_name'],
        'timestamp': '2024-01-15T00:00:00Z'
    })

urlpatterns = [
    # Home page
    path('', HomeView.as_view(), name='home'),
    path('api/', home_api, name='home_api'),
    
    # Admin
    path(f'{settings.ADMIN_URL}', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health_check'),
    
    # Payment routes (both web and API)
    path('payments/', include('payments.urls')),  # Payment URL for Flutter app
    path('callbacks/', include('callbacks.urls')),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/firebase/', include('firebase_sync.urls')),
    
    # Web routes (for payment forms accessed from Flutter)
    # path('payment/', include('payments.web_urls')), # Removed - using main payments URLs
]

# Serve static files in development
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
