"""
URL configuration for SalesSmart project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from pos import views as pos_views
from pos.sitemap import StaticViewSitemap, BusinessSitemap, ProductSitemap, CategorySitemap

# Sitemap configuration
sitemaps = {
    'static': StaticViewSitemap,
    'businesses': BusinessSitemap,
    'products': ProductSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', pos_views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login', http_method_names=['get', 'post']), name='logout'),
    
    # Marketing and Authentication (no business prefix)
    path('', pos_views.marketing_page, name='marketing'),
    path('signup/', pos_views.signup, name='signup'),
    path('verify-email/', pos_views.verify_email, name='verify_email'),
    path('google-signup/', pos_views.google_signup, name='google_signup'),
    
    # Business-specific URLs - include pos.urls directly
    path('', include('pos.urls')),
    
    path('superadmin/', include('superadmin.urls')),
    
    # Google Site Verification
    path('googlea3eacb9da093fb9c.html', pos_views.google_verification),
    
    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
