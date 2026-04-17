from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from pos.models import Business, Product, Category

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['marketing', 'signup', 'login']

    def location(self, item):
        return reverse(item)

class BusinessSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Business.objects.filter(is_active=True).order_by('created_at')

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return f'/business/{obj.id}/'

class ProductSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True).order_by('updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f'/product/{obj.id}/'

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Category.objects.filter(is_active=True).order_by('created_at')

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return f'/category/{obj.id}/'
