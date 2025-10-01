"""
Bematore Payment System - Error Views
Professional Error Handling Views
Developed by Brandon Ochieng | Bematore Technologies

Custom error views for professional error page handling
with consistent Bematore branding and design.
"""

from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError, HttpResponseForbidden, HttpResponseBadRequest


def handler404(request, exception):
    """
    Custom 404 error handler
    """
    return render(request, '404.html', {
        'request_path': request.path,
    }, status=404)


def handler500(request):
    """
    Custom 500 error handler
    """
    return render(request, '500.html', {
        'request_path': request.path,
    }, status=500)


def handler403(request, exception):
    """
    Custom 403 error handler
    """
    return render(request, '403.html', {
        'request_path': request.path,
    }, status=403)


def handler400(request, exception):
    """
    Custom 400 error handler
    """
    return render(request, '400.html', {
        'request_path': request.path,
    }, status=400)


def custom_error_view(request, status_code=500, error_title="Error", error_message="An error occurred"):
    """
    Generic error view for custom error handling
    """
    return render(request, 'error.html', {
        'status_code': status_code,
        'error_title': error_title,
        'error_message': error_message,
        'request_path': request.path,
    }, status=status_code)


# Test views for error pages (only in development)
def test_404(request):
    """Test 404 page - development only"""
    return render(request, '404.html', status=404)


def test_500(request):
    """Test 500 page - development only"""
    return render(request, '500.html', status=500)


def test_403(request):
    """Test 403 page - development only"""
    return render(request, '403.html', status=403)


def test_400(request):
    """Test 400 page - development only"""
    return render(request, '400.html', status=400)