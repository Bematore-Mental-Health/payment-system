"""
Main URL Configuration for Bematore Payment System
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'bematore-payment-system',
        'version': '1.0.0'
    })

urlpatterns = [
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
