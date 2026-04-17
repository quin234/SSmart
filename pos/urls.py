from django.urls import path, re_path
from . import views

app_name = 'pos'

urlpatterns = [
    # Marketing and Authentication
    re_path(r'^$', views.marketing_page, name='marketing'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('signup/', views.signup, name='signup'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('google-signup/', views.google_signup, name='google_signup'),
    
    # Dashboard - main app entry point after login
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Generic create handler - redirect to appropriate create page or show error
    path('create/', views.generic_create_handler, name='generic_create'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Sales
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/create/', views.create_sale, name='create_sale'),
    path('sales/mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    
    # Point of Sale
    path('pos/', views.pos_interface, name='pos_interface'),
    
    # Reports and Analytics
    path('reports/', views.reports, name='reports'),
    path('profit-loss/', views.profit_loss, name='profit_loss'),
    path('inventory/', views.inventory_management, name='inventory_management'),
    path('reports/sales/', views.sales_report, name='sales_report'),
    
    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    
    # Business Management
    path('business/profile/', views.business_profile, name='business_profile'),
    path('business/settings/', views.business_settings, name='business_settings'),
    path('business/users/', views.user_list, name='user_list'),
    path('business/users/create/', views.user_create, name='user_create'),
    path('business/users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('business/users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    # Database Management
    path('database/', views.database_management, name='database_management'),
    path('database/backup/', views.database_backup, name='database_backup'),
    path('database/restore/', views.database_restore, name='database_restore'),
    path('database/clear/', views.database_clear, name='database_clear'),
]
