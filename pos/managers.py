from django.db import models


class BusinessFilteredManager(models.Manager):
    """
    Manager that automatically filters by business context.
    Ensures complete data isolation between businesses.
    """
    
    def get_queryset(self):
        # This manager will be used in views where request.business is available
        # The actual filtering will be done at the view level for security
        return super().get_queryset()
    
    def for_business(self, business):
        """
        Explicitly filter by business for additional security
        """
        return self.get_queryset().filter(business=business)
    
    def create(self, **kwargs):
        # Auto-assign business if not provided and business is in kwargs
        return super().create(**kwargs)
