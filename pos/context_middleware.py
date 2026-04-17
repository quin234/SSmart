from threading import local


class RequestContextMiddleware:
    """
    Middleware to store request in thread-local storage
    for use by custom managers.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Store request in thread-local storage
        local.request = request
        
        response = self.get_response(request)
        
        # Clean up thread-local storage
        try:
            del local.request
        except AttributeError:
            pass
        
        return response
