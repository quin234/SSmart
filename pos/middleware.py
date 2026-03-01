from django.shortcuts import redirect
from django.http import Http404
from .models import Business


class BusinessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extract business from subdomain or URL path
        host = request.META.get('HTTP_HOST', '')
        
        # For development, we'll use path-based approach
        # In production, you might want to use subdomain approach
        path_parts = request.path.strip('/').split('/')
        
        request.business = None
        
        # Try to get business from first path segment
        if len(path_parts) > 0 and path_parts[0]:
            try:
                business = Business.objects.get(subdomain=path_parts[0], is_active=True)
                request.business = business
            except Business.DoesNotExist:
                pass
        
        # Alternative: Try subdomain approach
        if not request.business and '.' in host:
            subdomain = host.split('.')[0]
            try:
                business = Business.objects.get(subdomain=subdomain, is_active=True)
                request.business = business
            except Business.DoesNotExist:
                pass
        
        # For authenticated users without business, assign them to a default business
        if request.user.is_authenticated and not request.business and not request.user.is_superuser:
            # Try to get the first business or create a default one
            try:
                business = Business.objects.first()
                if business:
                    request.business = business
            except:
                pass
        
        response = self.get_response(request)
        return response


class UserRoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add user role information to request
        if request.user.is_authenticated:
            request.user_role = getattr(request.user, 'role', 'Cashier')
            request.is_business_admin = getattr(request.user, 'is_business_admin', False)
        else:
            request.user_role = None
            request.is_business_admin = False
        
        response = self.get_response(request)
        return response
