from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import re
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from .models import Business, User, Category, Product, Sale, SaleItem, Expense
from .forms import (
    ProductForm, CategoryForm, SaleForm, ExpenseForm, 
    BusinessForm, UserCreationForm, UserEditForm
)


@login_required
def dashboard(request):
    # Handle superuser or users without business
    if not request.business and not request.user.is_superuser:
        # Try to assign user to first available business
        first_business = Business.objects.first()
        if first_business:
            request.user.business = first_business
            request.user.save()
            request.business = first_business
        else:
            # No businesses exist, redirect to admin to create one
            return redirect('/admin/')
    
    if request.user.is_superuser and not request.business:
        # Superuser sees admin interface or business selection
        return redirect('/admin/')
    
    # Get business-specific statistics
    today = timezone.now().date()
    this_month = today.replace(day=1)
    
    # Total statistics
    total_products = Product.objects.filter(business=request.business).count()
    total_sales = Sale.objects.filter(business=request.business).count()
    total_revenue = Sale.objects.filter(business=request.business).aggregate(total=Sum('total_amount'))['total'] or 0
    low_stock_products = Product.objects.filter(
        business=request.business,
        stock_quantity__lte=F('low_stock_threshold')
    ).count()
    
    # Sales statistics
    today_sales = Sale.objects.filter(
        business=request.business,
        sale_date__date=today
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    month_sales = Sale.objects.filter(
        business=request.business,
        sale_date__date__gte=this_month
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    # Recent sales
    recent_sales = Sale.objects.filter(
        business=request.business
    ).order_by('-sale_date')[:10]
    
    # Low stock products list
    low_stock_products_list = Product.objects.filter(
        business=request.business,
        stock_quantity__lte=F('low_stock_threshold')
    ).order_by('stock_quantity')[:10]
    
    # Top products
    top_products = Product.objects.filter(
        business=request.business
    ).annotate(
        total_sold=Sum('saleitem__quantity')
    ).order_by('-total_sold')[:10]
    
    context = {
        'total_products': total_products,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'low_stock_products': low_stock_products,
        'today_sales': today_sales,
        'month_sales': month_sales,
        'recent_sales': recent_sales,
        'low_stock_products_list': low_stock_products_list,
        'top_products': top_products,
    }
    return render(request, 'pos/dashboard.html', context)


@login_required
def product_list(request):
    if not request.business:
        return redirect('admin/')
    
    products = Product.objects.filter(business=request.business)
    categories = Category.objects.filter(business=request.business)
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Search
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(barcode__icontains=search)
        )
    
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'pos/product_list.html', context)


@login_required
def product_create(request):
    if not request.business:
        return redirect('admin/')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.business = request.business
            product.save()
            messages.success(request, 'Product created successfully!')
            return redirect('pos:product_list')
    else:
        form = ProductForm()
        # Filter categories by business
        form.fields['category'].queryset = Category.objects.filter(business=request.business)
    
    return render(request, 'pos/product_form.html', {'form': form, 'title': 'Create Product'})


@login_required
def product_edit(request, pk):
    if not request.business:
        return redirect('admin/')
    
    product = get_object_or_404(Product, pk=pk, business=request.business)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('pos:product_list')
    else:
        form = ProductForm(instance=product)
        form.fields['category'].queryset = Category.objects.filter(business=request.business)
    
    return render(request, 'pos/product_form.html', {'form': form, 'title': 'Edit Product'})


@login_required
def product_delete(request, pk):
    if not request.business:
        return redirect('admin/')
    
    product = get_object_or_404(Product, pk=pk, business=request.business)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('pos:product_list')
    
    return render(request, 'pos/delete_confirm.html', {'object': product, 'type': 'Product'})


@login_required
def category_list(request):
    if not request.business:
        return redirect('admin/')
    
    categories = Category.objects.filter(business=request.business)
    return render(request, 'pos/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    if not request.business:
        return redirect('admin/')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.business = request.business
            category.save()
            messages.success(request, 'Category created successfully!')
            return redirect('pos:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'pos/category_form.html', {'form': form, 'title': 'Create Category'})


@login_required
def category_edit(request, pk):
    if not request.business:
        return redirect('admin/')
    
    category = get_object_or_404(Category, pk=pk, business=request.business)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('pos:category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'pos/category_form.html', {'form': form, 'title': 'Edit Category'})


@login_required
def category_delete(request, pk):
    if not request.business:
        return redirect('admin/')
    
    category = get_object_or_404(Category, pk=pk, business=request.business)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('pos:category_list')
    
    return render(request, 'pos/delete_confirm.html', {'object': category, 'type': 'Category'})


@login_required
def sale_list(request):
    if not request.business:
        return redirect('admin/')
    
    sales = Sale.objects.filter(business=request.business).order_by('-sale_date')
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        sales = sales.filter(sale_date__date__gte=start_date)
    if end_date:
        sales = sales.filter(sale_date__date__lte=end_date)
    
    context = {'sales': sales}
    return render(request, 'pos/sale_list.html', context)


@login_required
def sale_detail(request, pk):
    if not request.business:
        return redirect('admin/')
    
    sale = get_object_or_404(Sale, pk=pk, business=request.business)
    return render(request, 'pos/sale_detail.html', {'sale': sale})


@login_required
def pos_interface(request):
    if not request.business:
        return redirect('admin/')
    
    products = Product.objects.filter(business=request.business, is_active=True)
    categories = Category.objects.filter(business=request.business, is_active=True)
    
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'pos/pos_interface.html', context)


@login_required
def reports(request):
    if not request.business:
        return redirect('admin/')
    
    return render(request, 'pos/reports.html')


@login_required
def sales_report(request):
    if not request.business:
        return redirect('admin/')
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).date()
    if not end_date:
        end_date = timezone.now().date()
    
    sales = Sale.objects.filter(
        business=request.business,
        sale_date__date__gte=start_date,
        sale_date__date__lte=end_date
    )
    
    # Aggregate data
    summary = sales.aggregate(
        total_sales=Sum('total_amount'),
        total_tax=Sum('tax_amount'),
        total_discount=Sum('discount_amount'),
        count=Count('id')
    )
    
    context = {
        'sales': sales,
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'pos/sales_report.html', context)


@login_required
def expense_list(request):
    if not request.business:
        return redirect('admin/')
    
    expenses = Expense.objects.filter(business=request.business).order_by('-expense_date')
    return render(request, 'pos/expense_list.html', {'expenses': expenses})


@login_required
def expense_create(request):
    if not request.business:
        return redirect('admin/')
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.business = request.business
            expense.created_by = request.user
            expense.save()
            messages.success(request, 'Expense created successfully!')
            return redirect('pos:expense_list')
    else:
        form = ExpenseForm()
    
    return render(request, 'pos/expense_form.html', {'form': form, 'title': 'Create Expense'})


@login_required
def business_profile(request):
    if not request.business:
        return redirect('admin/')
    
    business = request.business
    
    if request.method == 'POST':
        form = BusinessForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, 'Business profile updated successfully!')
            return redirect('pos:business_profile')
    else:
        form = BusinessForm(instance=business)
    
    return render(request, 'pos/business_profile.html', {'form': form})


@login_required
def user_list(request):
    if not request.business or not request.user.is_business_admin:
        messages.error(request, 'You do not have permission to view users.')
        return redirect('pos:dashboard')
    
    users = User.objects.filter(business=request.business)
    return render(request, 'pos/user_list.html', {'users': users})


@login_required
def user_create(request):
    if not request.business or not request.user.is_business_admin:
        messages.error(request, 'You do not have permission to create users.')
        return redirect('pos:dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.business = request.business
            user.save()
            messages.success(request, 'User created successfully!')
            return redirect('pos:user_list')
    else:
        form = UserCreationForm()
    
    return render(request, 'pos/user_form.html', {'form': form, 'title': 'Create User'})


@login_required
def expense_edit(request, pk):
    if not request.business or not request.user.is_business_admin:
        messages.error(request, 'You do not have permission to edit expenses.')
        return redirect('pos:dashboard')
    
    expense = get_object_or_404(Expense, pk=pk, business=request.business)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('pos:expense_list')
    else:
        form = ExpenseForm(instance=expense)
    
    return render(request, 'pos/expense_form.html', {'form': form, 'title': 'Edit Expense'})


@login_required
def expense_delete(request, pk):
    if not request.business or not request.user.is_business_admin:
        messages.error(request, 'You do not have permission to delete expenses.')
        return redirect('pos:dashboard')
    
    expense = get_object_or_404(Expense, pk=pk, business=request.business)
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('pos:expense_list')
    
    return render(request, 'pos/delete_confirm.html', {'object': expense, 'type': 'Expense'})


def marketing_page(request):
    """Marketing landing page"""
    return render(request, 'pos/marketing.html')


def signup(request):
    """Handle user signup with email verification"""
    if request.method == 'POST':
        business_name = request.POST.get('businessName')
        full_name = request.POST.get('fullName')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        # Validate password strength
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return redirect('pos:marketing')
        
        if not re.search(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', password):
            messages.error(request, 'Password must contain uppercase, lowercase, and numbers')
            return redirect('pos:marketing')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('pos:marketing')
        
        try:
            # Create business
            business = Business.objects.create(
                name=business_name,
                email=email,
                phone=phone,
                subscription_plan='Basic'  # Default plan
            )
            
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=full_name.split()[0] if full_name else '',
                last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
                business=business,
                is_business_admin=True
            )
            
            # Generate verification code
            verification_code = ''.join(random.choices(string.digits, k=6))
            
            # Send verification email (in production, use actual email sending)
            try:
                send_mail(
                    'Verify your SalesSmart account',
                    f'Your verification code is: {verification_code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
            except:
                # For demo purposes, store code in session
                request.session['verification_code'] = verification_code
                request.session['user_id'] = user.id
            
            messages.success(request, 'Account created! Please check your email for verification code.')
            return render(request, 'pos/verify_email.html', {'email': email})
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('pos:marketing')
    
    return redirect('pos:marketing')


def verify_email(request):
    """Handle email verification"""
    if request.method == 'POST':
        code = request.POST.get('verificationCode')
        email = request.POST.get('email')
        
        # For demo, check session or use hardcoded code
        stored_code = request.session.get('verification_code', '123456')
        
        if code == stored_code:
            # Activate user account
            user_id = request.session.get('user_id')
            if user_id:
                user = User.objects.get(id=user_id)
                user.is_active = True
                user.save()
                
                # Clean session
                del request.session['verification_code']
                del request.session['user_id']
                
                # Log user in
                login(request, user)
                messages.success(request, 'Account verified successfully!')
                return redirect('pos:dashboard')
        
        messages.error(request, 'Invalid verification code')
        return render(request, 'pos/verify_email.html', {'email': email})
    
    return redirect('pos:marketing')


def google_signup(request):
    """Handle Google OAuth signup (placeholder)"""
    messages.info(request, 'Google signup integration coming soon!')
    return redirect('pos:marketing')
