from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def business_required(view_func):
    """
    Decorator to ensure user has access to business context
    and all data operations are properly scoped to their business.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Remove business_subdomain from kwargs if present (from URL pattern)
        kwargs.pop('business_subdomain', None)
        
        # Check if view requires business context (skip for public pages)
        public_views = ['marketing_page', 'signup', 'verify_email', 'google_signup']
        view_name = view_func.__name__
        
        # Ensure user is authenticated for non-public views
        if view_name not in public_views:
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Ensure user has business assigned
            if not request.user.is_superuser and not request.user.business:
                messages.error(request, 'You are not assigned to any business.')
                return redirect('login')
            
            # Ensure business context is set
            if not request.user.is_superuser and not request.business:
                if request.user.business:
                    request.business = request.user.business
                else:
                    messages.error(request, 'No business context found.')
                    return redirect('login')
            
            # Verify user belongs to current business (if business is set)
            if not request.user.is_superuser and request.business:
                if request.user.business != request.business:
                    messages.error(request, 'You do not have access to this business.')
                    return redirect(f'/{request.user.business.subdomain}/')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def business_admin_required(view_func):
    """
    Decorator to ensure user is business admin or superuser.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.user.is_superuser or request.user.is_business_admin):
            messages.error(request, 'You need business admin privileges to access this page.')
            return redirect('pos:dashboard')
        
        return business_required(view_func)(request, *args, **kwargs)
    
    return _wrapped_view
