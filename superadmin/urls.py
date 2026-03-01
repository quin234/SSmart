from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    path('login/', views.superadmin_login, name='login'),
    path('logout/', views.superadmin_logout, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('businesses/', views.businesses_list, name='businesses_list'),
    path('business/<int:business_id>/', views.business_detail, name='business_detail'),
    path('business/<int:business_id>/toggle/', views.toggle_business_status, name='toggle_business_status'),
    path('business/<int:business_id>/request-upgrade/', views.request_upgrade, name='request_upgrade'),
    path('users/', views.users_list, name='users_list'),
    path('analytics/', views.analytics, name='analytics'),
]
