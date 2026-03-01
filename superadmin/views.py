from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from pos.models import Business, User, Category, Product, Sale, SaleItem, Expense
from django.db.models import Count, Sum, Q
from django.http import JsonResponse

def superadmin_login(request):
    """Superadmin login view"""
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('superadmin:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            messages.success(request, 'Welcome to SuperAdmin Portal')
            return redirect('superadmin:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')
    
    return render(request, 'superadmin/login.html')

def superadmin_logout(request):
    """Superadmin logout view"""
    logout(request)
    messages.info(request, 'You have been logged out')
    return redirect('superadmin:login')

@login_required(login_url='superadmin:login')
def dashboard(request):
    """Superadmin dashboard"""
    if not request.user.is_superuser:
        return redirect('superadmin:login')
    
    # Get business statistics
    total_businesses = Business.objects.count()
    active_businesses = Business.objects.filter(is_active=True).count()
    inactive_businesses = total_businesses - active_businesses
    
    # Get user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Get recent businesses
    recent_businesses = Business.objects.order_by('-created_at')[:10]
    
    # Get businesses by subscription plan
    free_plan = Business.objects.filter(subscription_plan='Free').count()
    pro_plan = Business.objects.filter(subscription_plan='Pro').count()
    enterprise_plan = Business.objects.filter(subscription_plan='Enterprise').count()
    
    # Calculate percentages
    free_percentage = (free_plan / total_businesses * 100) if total_businesses > 0 else 0
    pro_percentage = (pro_plan / total_businesses * 100) if total_businesses > 0 else 0
    enterprise_percentage = (enterprise_plan / total_businesses * 100) if total_businesses > 0 else 0
    
    context = {
        'total_businesses': total_businesses,
        'active_businesses': active_businesses,
        'inactive_businesses': inactive_businesses,
        'total_users': total_users,
        'active_users': active_users,
        'recent_businesses': recent_businesses,
        'free_plan': free_plan,
        'pro_plan': pro_plan,
        'enterprise_plan': enterprise_plan,
        'free_percentage': free_percentage,
        'pro_percentage': pro_percentage,
        'enterprise_percentage': enterprise_percentage,
    }
    
    return render(request, 'superadmin/dashboard.html', context)

@login_required(login_url='superadmin:login')
def businesses_list(request):
    """List all businesses"""
    if not request.user.is_superuser:
        return redirect('superadmin:login')
    
    businesses = Business.objects.all().order_by('-created_at')
    
    # Calculate duration for each business
    for business in businesses:
        if business.created_at:
            duration = timezone.now() - business.created_at
            business.duration_days = duration.days
            business.duration_months = duration.days // 30
        else:
            business.duration_days = 0
            business.duration_months = 0
    
    # Calculate statistics
    active_businesses_count = businesses.filter(is_active=True).count()
    most_common_plan_data = businesses.values('subscription_plan').annotate(count=Count('subscription_plan')).order_by('-count').first()
    most_common_plan = most_common_plan_data['subscription_plan'] if most_common_plan_data else 'None'
    oldest_business = businesses.order_by('created_at').first()
    
    context = {
        'businesses': businesses,
        'active_businesses_count': active_businesses_count,
        'most_common_plan': most_common_plan,
        'oldest_business': oldest_business,
    }
    
    return render(request, 'superadmin/businesses_list.html', context)

@login_required(login_url='superadmin:login')
def business_detail(request, business_id):
    """Business detail view"""
    if not request.user.is_superuser:
        return redirect('superadmin:login')
    
    business = get_object_or_404(Business, id=business_id)
    
    # Get business statistics
    users_count = User.objects.filter(business=business).count()
    categories_count = Category.objects.filter(business=business).count()
    products_count = Product.objects.filter(business=business).count()
    sales_count = Sale.objects.filter(business=business).count()
    expenses_count = Expense.objects.filter(business=business).count()
    
    # Get recent sales
    recent_sales = Sale.objects.filter(business=business).order_by('-created_at')[:10]
    
    # Calculate duration
    if business.created_at:
        duration = timezone.now() - business.created_at
        duration_days = duration.days
        duration_months = duration.days // 30
    else:
        duration_days = 0
        duration_months = 0
    
    context = {
        'business': business,
        'users_count': users_count,
        'categories_count': categories_count,
        'products_count': products_count,
        'sales_count': sales_count,
        'expenses_count': expenses_count,
        'recent_sales': recent_sales,
        'duration_days': duration_days,
        'duration_months': duration_months,
    }
    
    return render(request, 'superadmin/business_detail.html', context)

@login_required(login_url='superadmin:login')
def toggle_business_status(request, business_id):
    """Toggle business active status"""
    if not request.user.is_superuser:
        return redirect('superadmin:login')
    
    if request.method == 'POST':
        business = get_object_or_404(Business, id=business_id)
        business.is_active = not business.is_active
        business.save()
        
        status = "activated" if business.is_active else "deactivated"
        messages.success(request, f'Business "{business.name}" has been {status}')
    
    return redirect('superadmin:businesses_list')

@login_required(login_url='superadmin:login')
def request_upgrade(request, business_id):
    """Send upgrade request to business"""
    if not request.user.is_superuser:
        return redirect('superadmin:login')
    
    business = get_object_or_404(Business, id=business_id)
    
    # Here you would typically send an email or notification
    # For now, we'll just show a success message
    messages.info(request, f'Upgrade request sent to "{business.name}". They will be notified via email.')
    
    return redirect('superadmin:business_detail', business_id=business_id)

@login_required(login_url='superadmin:login')
def users_list(request):
    """List all users across all businesses"""
    if not request.user.is_superuser:
        return redirect('superadmin:login')
    
    users = User.objects.all().order_by('-date_joined')
    
    # Calculate statistics
    active_users_count = users.filter(is_active=True).count()
    super_users_count = users.filter(is_superuser=True).count()
    business_admins_count = users.filter(is_business_admin=True).count()
    
    context = {
        'users': users,
        'active_users_count': active_users_count,
        'super_users_count': super_users_count,
        'business_admins_count': business_admins_count,
    }
    
    return render(request, 'superadmin/users_list.html', context)

@login_required(login_url='superadmin:login')
def analytics(request):
    """Analytics dashboard"""
    if not request.user.is_superuser:
        return redirect('superadmin:login')
    
    # Get business growth data
    last_30_days = timezone.now() - timedelta(days=30)
    recent_businesses = Business.objects.filter(created_at__gte=last_30_days).count()
    
    # Get top businesses by activity
    top_businesses_queryset = Business.objects.annotate(
        user_count=Count('user'),
        product_count=Count('product')
    ).order_by('-user_count')
    
    # Get all top businesses for filtering
    all_top_businesses = top_businesses_queryset[:10]
    
    # Calculate additional statistics
    max_users_per_business = 0
    max_products_per_business = 0
    
    if all_top_businesses:
        max_users_per_business = max(business.user_count for business in all_top_businesses)
        max_products_per_business = max(business.product_count for business in all_top_businesses)
    
    # Calculate plan distribution from the full queryset before slicing
    plan_distribution = top_businesses_queryset.values('subscription_plan').annotate(count=Count('subscription_plan'))
    free_plan_count = plan_distribution.filter(subscription_plan='Free').first()['count'] if plan_distribution.filter(subscription_plan='Free').exists() else 0
    pro_plan_count = plan_distribution.filter(subscription_plan='Pro').first()['count'] if plan_distribution.filter(subscription_plan='Pro').exists() else 0
    enterprise_plan_count = plan_distribution.filter(subscription_plan='Enterprise').first()['count'] if plan_distribution.filter(subscription_plan='Enterprise').exists() else 0
    
    context = {
        'recent_businesses': recent_businesses,
        'top_businesses': all_top_businesses,
        'max_users_per_business': max_users_per_business,
        'max_products_per_business': max_products_per_business,
        'free_plan_count': free_plan_count,
        'pro_plan_count': pro_plan_count,
        'enterprise_plan_count': enterprise_plan_count,
    }
    
    return render(request, 'superadmin/analytics.html', context)
