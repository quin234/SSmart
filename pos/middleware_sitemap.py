class SitemapMiddleware:
    """
    Middleware to handle sitemap-specific headers and caching
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Remove noindex headers for sitemap requests
        if request.path == '/sitemap.xml':
            # Remove any X-Robots-Tag headers that might contain noindex
            if 'X-Robots-Tag' in response:
                del response['X-Robots-Tag']
            
            # Set proper robots header for sitemap
            response['X-Robots-Tag'] = 'all'
            
            # Set cache headers for sitemap
            response['Cache-Control'] = 'public, max-age=3600'
        
        return response
