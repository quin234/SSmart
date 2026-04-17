from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib import messages
from django.db.models import Sum, Count, Avg, F, Q, Max
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.core.management import call_command
from django.http import HttpResponse, JsonResponse, FileResponse
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import os
import tempfile
import re
import random
import string
from .models import Business, User, Category, Product, Sale, SaleItem, Expense
from .forms import (
    ProductForm, CategoryForm, SaleForm, ExpenseForm, 
    BusinessForm, BusinessSettingsForm, UserCreationForm, UserEditForm
)
from .decorators import business_required, business_admin_required


class CustomLoginView(DjangoLoginView):
    """Custom login view that passes business context to the template"""
    template_name = 'pos/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Try to get business from request (set by middleware)
        if hasattr(self.request, 'business') and self.request.business:
            context['business_name'] = self.request.business.name
        else:
            # Fallback to default name if no business context
            context['business_name'] = 'SalesSmart'
        return context
    
    def form_valid(self, form):
        # Call the parent form_valid method to handle login
        response = super().form_valid(form)
        
        # Ensure business context is set after login
        if self.request.user.is_authenticated and hasattr(self.request.user, 'business'):
            if self.request.user.business and not hasattr(self.request, 'business'):
                self.request.business = self.request.user.business
        
        return response


@business_required
def dashboard(request):
    # Handle superuser without business context
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
    
    # Chart data - Daily sales for last 7 days
    daily_sales_data = []
    for i in range(7):
        date = today - timedelta(days=i)
        sales = Sale.objects.filter(
            business=request.business,
            sale_date__date=date
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        daily_sales_data.append({
            'date': date.strftime('%b %d'),
            'amount': float(sales)
        })
    daily_sales_data.reverse()
    
    # Chart data - Monthly sales for last 6 months
    monthly_sales_data = []
    for i in range(6):
        month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        sales = Sale.objects.filter(
            business=request.business,
            sale_date__date__gte=month_start,
            sale_date__date__lte=month_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        monthly_sales_data.append({
            'month': month_start.strftime('%b'),
            'amount': float(sales)
        })
    monthly_sales_data.reverse()
    
    # Top products data for chart
    top_products_data = []
    for product in top_products[:5]:
        top_products_data.append({
            'name': product.name,
            'sold': product.total_sold or 0
        })
    
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
        'daily_sales_data': daily_sales_data,
        'monthly_sales_data': monthly_sales_data,
        'top_products_data': top_products_data,
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
            try:
                product.save()
                messages.success(request, 'Product created successfully!')
                return redirect('pos:product_list')
            except Exception as e:
                if 'UNIQUE constraint failed' in str(e):
                    form.add_error('name', 'A product with this name already exists for your business.')
                else:
                    messages.error(request, f'Error creating product: {str(e)}')
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
            try:
                form.save()
                messages.success(request, 'Product updated successfully!')
                return redirect('pos:product_list')
            except Exception as e:
                if 'UNIQUE constraint failed' in str(e):
                    form.add_error('name', 'A product with this name already exists for your business.')
                else:
                    messages.error(request, f'Error updating product: {str(e)}')
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
            try:
                category.save()
                messages.success(request, 'Category created successfully!')
                return redirect('pos:category_list')
            except Exception as e:
                if 'UNIQUE constraint failed' in str(e):
                    form.add_error('name', 'A category with this name already exists for your business.')
                else:
                    messages.error(request, f'Error creating category: {str(e)}')
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
            try:
                form.save()
                messages.success(request, 'Category updated successfully!')
                return redirect('pos:category_list')
            except Exception as e:
                if 'UNIQUE constraint failed' in str(e):
                    form.add_error('name', 'A category with this name already exists for your business.')
                else:
                    messages.error(request, f'Error updating category: {str(e)}')
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


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .daraja import process_mpesa_callback
import json


@csrf_exempt
def mpesa_callback(request):
    """Handle M-Pesa callback from Daraja API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        # Parse callback data
        callback_data = json.loads(request.body)
        
        # Process the callback
        result = process_mpesa_callback(callback_data)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'M-Pesa callback processed successfully',
                'sale_number': result.get('sale_number'),
                'payment_status': result.get('payment_status')
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid callback data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Callback processing error: {str(e)}'})


@login_required
def google_signup(request):
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
    
    # Calculate total quantity
    total_quantity = sum(item.quantity for item in sale.items.all())
    
    return render(request, 'pos/sale_detail.html', {
        'sale': sale,
        'total_quantity': total_quantity
    })


@login_required
def pos_interface(request):
    if not request.business:
        return redirect('admin/')
    
    products = Product.objects.filter(business=request.business, is_active=True)
    categories = Category.objects.filter(business=request.business, is_active=True)
    
    context = {
        'products': products,
        'categories': categories,
        'business': request.business,
        'enable_tax': request.business.enable_tax,
        'tax_rate': float(request.business.tax_rate),
        'tax_name': request.business.tax_name,
        'enable_daraja': request.business.enable_daraja,
    }
    return render(request, 'pos/pos_interface.html', context)


@login_required
def profit_loss(request):
    """Handle profit/loss analysis"""
    if not request.business:
        return redirect('admin/')
    
    today = timezone.now().date()
    this_month = today.replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    
    # Calculate profit/loss for current month
    sales_data = Sale.objects.filter(
        business=request.business,
        sale_date__date__gte=this_month
    ).aggregate(
        total_sales=Sum('total_amount'),
        total_cost=Sum('items__cost_price')
    )
    
    # Calculate profit/loss for last month
    last_month_sales = Sale.objects.filter(
        business=request.business,
        sale_date__date__gte=last_month,
        sale_date__date__lt=this_month
    ).aggregate(
        total_sales=Sum('total_amount'),
        total_cost=Sum('items__cost_price')
    )
    
    # Calculate current month profit/loss
    current_revenue = sales_data['total_sales'] or Decimal('0')
    current_cost = sales_data['total_cost'] or Decimal('0')
    current_profit = current_revenue - current_cost
    current_profit_margin = (current_profit / current_revenue * 100) if current_revenue > 0 else 0
    
    # Calculate last month profit/loss
    last_revenue = last_month_sales['total_sales'] or Decimal('0')
    last_cost = last_month_sales['total_cost'] or Decimal('0')
    last_profit = last_revenue - last_cost
    last_profit_margin = (last_profit / last_revenue * 100) if last_revenue > 0 else 0
    
    # Calculate monthly profit/loss for last 6 months
    monthly_data = []
    for i in range(6):
        month_start = (this_month - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_sales = Sale.objects.filter(
            business=request.business,
            sale_date__date__gte=month_start,
            sale_date__date__lte=month_end
        ).aggregate(
            revenue=Sum('total_amount'),
            cost=Sum('items__cost_price')
        )
        
        revenue = month_sales['revenue'] or Decimal('0')
        cost = month_sales['cost'] or Decimal('0')
        profit = revenue - cost
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(revenue),
            'cost': float(cost),
            'profit': float(profit),
            'profit_margin': float((profit / revenue * 100) if revenue > 0 else 0)
        })
    
    monthly_data.reverse()
    
    # Top profitable products
    top_products = Product.objects.filter(
        business=request.business
    ).annotate(
        total_revenue=Sum('saleitem__total_price'),
        total_cost=Sum('saleitem__cost_price'),
        total_profit=Sum('saleitem__total_price') - Sum('saleitem__cost_price'),
        quantity_sold=Sum('saleitem__quantity')
    ).filter(
        quantity_sold__gt=0
    ).order_by('-total_profit')[:10]
    
    # Calculate growth percentages
    revenue_growth = ((current_revenue - last_revenue) / last_revenue * 100) if last_revenue > 0 else 0
    profit_growth = ((current_profit - last_profit) / last_profit * 100) if last_profit != 0 else 0
    
    context = {
        'current_revenue': float(current_revenue),
        'current_cost': float(current_cost),
        'current_profit': float(current_profit),
        'current_profit_margin': float(current_profit_margin),
        'last_revenue': float(last_revenue),
        'last_cost': float(last_cost),
        'last_profit': float(last_profit),
        'last_profit_margin': float(last_profit_margin),
        'revenue_growth': float(revenue_growth),
        'revenue_growth_abs': float(abs(revenue_growth)),
        'profit_growth': float(profit_growth),
        'profit_growth_abs': float(abs(profit_growth)),
        'monthly_data': monthly_data,
        'top_products': top_products,
    }
    
    return render(request, 'pos/profit_loss.html', context)


@login_required
def inventory_management(request):
    """Handle inventory management with smart restocking"""
    if not request.business:
        return redirect('admin/')
    
    # Get all products with basic stock information
    products = Product.objects.filter(business=request.business).order_by('stock_quantity')
    
    # Calculate restocking recommendations
    restock_recommendations = []
    for product in products:
        # Calculate total sold manually
        total_sold = 0
        try:
            from pos.models import SaleItem
            total_sold = SaleItem.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
        except:
            total_sold = 0
            
        stock_quantity = product.stock_quantity
        low_stock_threshold = product.low_stock_threshold
        
        # Calculate days since last sale
        days_since_last_sale = None
        try:
            last_sale = SaleItem.objects.filter(product=product).order_by('-sale__sale_date').first()
            if last_sale and last_sale.sale:
                days_since_last_sale = (timezone.now().date() - last_sale.sale.sale_date.date()).days
        except:
            days_since_last_sale = None
        
        # Smart restocking logic
        recommendation = {
            'product': product,
            'current_stock': stock_quantity,
            'total_sold': total_sold,
            'status': 'normal',
            'suggested_order': 0,
            'urgency': 'low',
            'reason': ''
        }
        
        # Low stock check
        if stock_quantity <= low_stock_threshold:
            recommendation['status'] = 'low_stock'
            recommendation['urgency'] = 'high'
            recommendation['suggested_order'] = max(getattr(product, 'reorder_quantity', None) or 10, low_stock_threshold * 2 - stock_quantity)
            recommendation['reason'] = f'Stock below threshold ({low_stock_threshold})'
        
        # Out of stock
        elif stock_quantity == 0:
            recommendation['status'] = 'out_of_stock'
            recommendation['urgency'] = 'critical'
            recommendation['suggested_order'] = getattr(product, 'reorder_quantity', None) or 20
            recommendation['reason'] = 'Product is out of stock'
        
        # High demand products
        elif total_sold > 50 and stock_quantity < total_sold * 0.5:
            recommendation['status'] = 'high_demand'
            recommendation['urgency'] = 'medium'
            recommendation['suggested_order'] = max(total_sold, stock_quantity)
            recommendation['reason'] = f'High demand ({total_sold} units sold)'
        
        # Slow moving products
        elif days_since_last_sale and days_since_last_sale > 30 and stock_quantity > 10:
            recommendation['status'] = 'slow_moving'
            recommendation['urgency'] = 'low'
            recommendation['suggested_order'] = 0
            recommendation['reason'] = f'No sales in {days_since_last_sale} days'
        
        restock_recommendations.append(recommendation)
    
    # Sort by urgency
    urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    restock_recommendations.sort(key=lambda x: urgency_order.get(x['urgency'], 4))
    
    # Inventory statistics
    total_products = products.count()
    low_stock_count = sum(1 for r in restock_recommendations if r['status'] in ['low_stock', 'out_of_stock'])
    out_of_stock_count = sum(1 for r in restock_recommendations if r['status'] == 'out_of_stock')
    total_stock_value = sum(p.stock_quantity * p.selling_price for p in products)
    
    context = {
        'restock_recommendations': restock_recommendations,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_stock_value': float(total_stock_value),
    }
    
    return render(request, 'pos/inventory_management.html', context)


@login_required
def reports(request):
    """Handle reports page"""
    if not request.business:
        return redirect('admin/')
    
    return render(request, 'pos/reports.html')


@login_required
@require_POST
@csrf_exempt
def create_sale(request):
    """Handle sale creation from POS interface"""
    if not request.business:
        return JsonResponse({'success': False, 'error': 'No business assigned'})
    
    try:
        data = json.loads(request.body)
        cart_items = data.get('cart', [])
        payment_method = data.get('payment_method', 'Cash')
        amount_tendered = Decimal(str(data.get('amount_tendered', 0)))
        mpesa_phone = data.get('mpesa_phone', '')
        use_daraja = data.get('use_daraja', False)
        
        # Use provided values or calculate based on business settings
        subtotal = Decimal(str(data.get('subtotal', 0)))
        tax_amount = Decimal(str(data.get('tax_amount', 0)))
        total_amount = Decimal(str(data.get('total_amount', 0)))
        
        # If values not provided, calculate them
        if not subtotal:
            subtotal = sum(Decimal(str(item['price'])) * item['quantity'] for item in cart_items)
            if request.business.enable_tax:
                tax_amount = subtotal * (request.business.tax_rate / Decimal('100'))
            total_amount = subtotal + tax_amount
        
        # For non-cash payments, set amount_tendered to total automatically
        if payment_method != 'Cash':
            amount_tendered = total_amount
        
        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Cart is empty'})
        
        # M-Pesa logic based on business settings
        if payment_method == 'M-Pesa':
            if request.business.enable_daraja:
                # M-Pesa is enabled - require phone number and use Daraja API
                if not mpesa_phone or len(mpesa_phone) != 10 or not mpesa_phone.isdigit():
                    return JsonResponse({'success': False, 'error': 'Valid M-Pesa phone number required (10 digits)'})
                
                # Validate Daraja settings
                from .daraja import validate_daraja_settings
                validation = validate_daraja_settings(request.business)
                if not validation['valid']:
                    return JsonResponse({'success': False, 'error': f"M-Pesa not configured: {validation['error']}"})
                
                # Create sale with pending status until M-Pesa confirmation
                sale = Sale.objects.create(
                    business=request.business,
                    cashier=request.user,
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    total_amount=total_amount,
                    payment_method=payment_method,
                    payment_status='Pending',
                    customer_phone=mpesa_phone,
                    notes='M-Pesa payment pending confirmation'
                )
                
                # Create sale items and update stock
                for item in cart_items:
                    product = Product.objects.get(id=item['id'], business=request.business)
                    
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=item['quantity'],
                        unit_price=Decimal(str(item['price'])),
                        total_price=Decimal(str(item['price'])) * item['quantity'],
                        cost_price=product.buying_price
                    )
                    
                    # Update product stock
                    product.stock_quantity -= item['quantity']
                    product.save()
                
                # Initiate M-Pesa STK Push
                from .daraja import DarajaAPI
                daraja = DarajaAPI(request.business)
                
                try:
                    # Format phone number for Daraja
                    formatted_phone = f"254{mpesa_phone[1:]}" if mpesa_phone.startswith('0') else mpesa_phone
                    
                    # Initiate STK Push
                    stk_result = daraja.stk_push(
                        phone_number=formatted_phone,
                        amount=int(total_amount),
                        account_reference=f"SALE-{sale.sale_number}",
                        transaction_desc=f"Payment for {sale.sale_number}"
                    )
                    
                    if stk_result['success']:
                        # Update sale with checkout request ID
                        sale.mpesa_transaction_id = stk_result['checkout_request_id']
                        sale.save()
                        
                        response_data = {
                            'success': True,
                            'sale_id': sale.id,
                            'sale_number': sale.sale_number,
                            'total_amount': float(total_amount),
                            'change': 0.00,
                            'message': 'M-Pesa payment initiated! Please check your phone to complete the payment.',
                            'mpesa_phone': mpesa_phone,
                            'mpesa_enabled': True,
                            'mpesa_transaction_id': stk_result['checkout_request_id'],
                            'payment_pending': True,
                            'checkout_request_id': stk_result['checkout_request_id']
                        }
                    else:
                        # M-Pesa initiation failed, mark sale as cancelled
                        sale.payment_status = 'Cancelled'
                        sale.notes = f"M-Pesa initiation failed: {stk_result['error']}"
                        sale.save()
                        
                        # Reverse stock changes
                        for item in cart_items:
                            product = Product.objects.get(id=item['id'], business=request.business)
                            product.stock_quantity += item['quantity']
                            product.save()
                        
                        return JsonResponse({'success': False, 'error': f"M-Pesa payment failed: {stk_result['error']}"})
                        
                except Exception as e:
                    # M-Pesa error, mark sale as cancelled and reverse stock
                    sale.payment_status = 'Cancelled'
                    sale.notes = f"M-Pesa error: {str(e)}"
                    sale.save()
                    
                    # Reverse stock changes
                    for item in cart_items:
                        product = Product.objects.get(id=item['id'], business=request.business)
                        product.stock_quantity += item['quantity']
                        product.save()
                    
                    logger.error(f"M-Pesa payment error for sale {sale.sale_number}: {e}")
                    return JsonResponse({'success': False, 'error': f"M-Pesa payment error: {str(e)}"})
                
                return JsonResponse(response_data)
                
            else:
                # M-Pesa is not enabled - complete sale assuming user sent money manually
                sale = Sale.objects.create(
                    business=request.business,
                    cashier=request.user,
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    total_amount=total_amount,
                    payment_method=payment_method,
                    payment_status='Paid',
                    notes='M-Pesa payment completed manually'
                )
        else:
            # Non-M-Pesa payment methods
            sale = Sale.objects.create(
                business=request.business,
                cashier=request.user,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                payment_method=payment_method,
                payment_status='Paid' if payment_method != 'Cash' or amount_tendered >= total_amount else 'Pending'
            )
        
        # Create sale items and update stock
        for item in cart_items:
            product = Product.objects.get(id=item['id'], business=request.business)
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=item['quantity'],
                unit_price=Decimal(str(item['price'])),
                total_price=Decimal(str(item['price'])) * item['quantity'],
                cost_price=product.buying_price
            )
            
            # Update product stock
            product.stock_quantity -= item['quantity']
            product.save()
        
        response_data = {
            'success': True,
            'sale_id': sale.id,
            'sale_number': sale.sale_number,
            'total_amount': float(total_amount),
            'change': float(amount_tendered - total_amount) if payment_method == 'Cash' else 0.00,
            'message': 'Sale completed successfully!',
            'mpesa_phone': mpesa_phone if payment_method == 'M-Pesa' and request.business.enable_daraja else None,
            'mpesa_enabled': request.business.enable_daraja,
            'mpesa_transaction_id': sale.mpesa_transaction_id if payment_method == 'M-Pesa' else None
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request data'})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'One or more products not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


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
def user_edit(request, pk):
    """Edit existing user"""
    if not request.business or not request.user.is_business_admin:
        messages.error(request, 'You do not have permission to edit users.')
        return redirect('pos:dashboard')
    
    user = get_object_or_404(User, pk=pk, business=request.business)
    
    # Prevent editing superusers or business admins if current user is not superuser
    if user.is_superuser or (user.is_business_admin and not request.user.is_superuser):
        messages.error(request, 'You do not have permission to edit this user.')
        return redirect('pos:user_list')
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully!')
            return redirect('pos:user_list')
    else:
        form = UserEditForm(instance=user)
    
    return render(request, 'pos/user_form.html', {'form': form, 'title': 'Edit User', 'user': user})


@login_required
def user_delete(request, pk):
    """Delete user"""
    if not request.business or not request.user.is_business_admin:
        messages.error(request, 'You do not have permission to delete users.')
        return redirect('pos:dashboard')
    
    user = get_object_or_404(User, pk=pk, business=request.business)
    
    # Prevent deleting superusers or business admins if current user is not superuser
    if user.is_superuser or (user.is_business_admin and not request.user.is_superuser):
        messages.error(request, 'You do not have permission to delete this user.')
        return redirect('pos:user_list')
    
    # Prevent self-deletion
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('pos:user_list')
    
    if request.method == 'POST':
        # Check if user has sales or other important data
        from pos.models import Sale
        user_sales = Sale.objects.filter(cashier=user).count()
        
        if user_sales > 0:
            messages.warning(request, f'Cannot delete user {user.username}. They have {user_sales} sales records. Consider deactivating instead.')
            return redirect('pos:user_list')
        
        user.delete()
        messages.success(request, f'User {user.username} deleted successfully!')
        return redirect('pos:user_list')
    
    return render(request, 'pos/delete_confirm.html', {'object': user, 'type': 'User', 'object_name': user.username})


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


@csrf_exempt
def generic_create_handler(request):
    """Generic handler for /create/ requests - redirects appropriately or shows error"""
    if request.method == 'POST':
        # Handle POST requests - try to determine what type of creation
        if request.content_type == 'application/json':
            # Likely a sale creation request
            return create_sale(request)
        else:
            # Redirect to appropriate create page based on user context
            if request.user.is_authenticated and request.business:
                # Default to product creation for authenticated users
                return redirect('pos:product_create')
            else:
                return redirect('login')
    
    # Handle GET requests
    if request.user.is_authenticated and request.business:
        # Show a create options page or redirect to default create page
        return redirect('pos:product_create')
    else:
        # Redirect to login for unauthenticated users
        return redirect('login')


def marketing_page(request):
    """Marketing landing page"""
    return render(request, 'pos/marketing.html')


def robots_txt(request):
    """Serve robots.txt file"""
    from django.template.loader import render_to_string
    content = render_to_string('pos/robots.txt', request=request)
    return HttpResponse(content, content_type='text/plain')


def google_verification(request):
    """Serve Google site verification file"""
    from django.conf import settings
    import os
    file_path = os.path.join(settings.BASE_DIR, 'googlea3eacb9da093fb9c.html')
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponseNotFound('Verification file not found')


def signup(request):
    """Handle user signup without email verification"""
    # Try to get business from request (set by middleware)
    business_name = 'SalesSmart'
    if hasattr(request, 'business') and request.business:
        business_name = request.business.name
    
    if request.method == 'POST':
        business_name = request.POST.get('businessName')
        full_name = request.POST.get('fullName')
        email = request.POST.get('email')
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')
        
        # Validate password confirmation
        if password != confirm_password:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Passwords do not match'})
            messages.error(request, 'Passwords do not match')
            return render(request, 'pos/marketing.html')  # Show marketing page with error

        # Validate password strength
        if len(password) < 8:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters long'})
            messages.error(request, 'Password must be at least 8 characters long')
            return render(request, 'pos/marketing.html')  # Show marketing page with error

        if not re.search(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', password):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Password must contain uppercase, lowercase, and numbers'})
            messages.error(request, 'Password must contain uppercase, lowercase, and numbers')
            return render(request, 'pos/marketing.html')  # Show marketing page with error

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Username already taken'})
            messages.error(request, 'Username already taken')
            return render(request, 'pos/marketing.html')  # Show marketing page with error

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Email already registered'})
            messages.error(request, 'Email already registered')
            return render(request, 'pos/marketing.html')  # Show marketing page with error

        try:
            # Create business
            business = Business.objects.create(
                name=business_name,
                email=email,
                phone=phone,
                subscription_plan='Basic'  # Default plan
            )

            # Create user as active immediately (no email verification needed)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=full_name.split()[0] if full_name else '',
                last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
                business=business,
                is_business_admin=True,
                is_active=True  # Activate immediately
            )

            # Log user in immediately
            login(request, user)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Account created successfully!', 'redirect': '/pos/dashboard/'})

            messages.success(request, 'Account created successfully! Welcome to SalesSmart!')
            return redirect('pos:dashboard')

        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': f'Error creating account: {str(e)}'})
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'pos/marketing.html')

    else:
        # GET request - show signup form
        return render(request, 'pos/signup.html', {'business_name': business_name})


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


@login_required
def business_settings(request):
    """Handle business settings including tax configuration"""
    if not request.business:
        messages.error(request, 'No business assigned')
        return redirect('pos:dashboard')
    
    business = request.business
    
    if request.method == 'POST':
        form = BusinessSettingsForm(request.POST, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, 'Business settings updated successfully!')
            return redirect('pos:business_settings')
    else:
        form = BusinessSettingsForm(instance=business)
    
    return render(request, 'pos/business_settings.html', {
        'form': form,
        'business': business,
        'title': 'Business Settings'
    })


@business_admin_required
def database_management(request):
    """Database management interface"""
    if not request.user.is_business_admin and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access database management')
        return redirect('pos:dashboard')
    
    # Get database statistics for current business only
    stats = {
        'products': Product.objects.filter(business=request.business).count(),
        'categories': Category.objects.filter(business=request.business).count(),
        'sales': Sale.objects.filter(business=request.business).count(),
        'expenses': Expense.objects.filter(business=request.business).count(),
    }
    
    return render(request, 'pos/database_management.html', {
        'stats': stats,
        'title': 'Database Management'
    })


@login_required
def database_backup(request):
    """Create and download database backup"""
    if not request.user.is_business_admin and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to create database backups')
        return redirect('pos:database_management')
    
    if request.method == 'POST':
        try:
            # Create temporary backup file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'db_backup_{timestamp}.sqlite3'
            
            # Create backup using management command
            backup_dir = tempfile.mkdtemp()
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copy database file
            db_path = settings.DATABASES['default']['NAME']
            import shutil
            shutil.copy2(db_path, backup_path)
            
            # Return file as download
            response = FileResponse(
                open(backup_path, 'rb'),
                as_attachment=True,
                filename=backup_filename
            )
            
            messages.success(request, 'Database backup downloaded successfully')
            return response
            
        except Exception as e:
            messages.error(request, f'Backup failed: {str(e)}')
    
    return redirect('pos:database_management')


@login_required
def database_restore(request):
    """Restore database from backup file"""
    if not request.user.is_business_admin and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to restore database')
        return redirect('pos:database_management')
    
    if request.method == 'POST':
        try:
            backup_file = request.FILES.get('backup_file')
            
            if not backup_file:
                messages.error(request, 'Please select a backup file')
                return redirect('pos:database_management')
            
            if not backup_file.name.endswith('.sqlite3'):
                messages.error(request, 'Invalid file format. Please select a .sqlite3 file')
                return redirect('pos:database_management')
            
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as temp_file:
                for chunk in backup_file.chunks():
                    temp_file.write(chunk)
                temp_backup_path = temp_file.name
            
            # Create safety backup of current database
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            db_path = settings.DATABASES['default']['NAME']
            safety_backup = os.path.join(
                os.path.dirname(db_path), 
                f'db_before_restore_{timestamp}.sqlite3'
            )
            import shutil
            shutil.copy2(db_path, safety_backup)
            
            # Restore from backup
            shutil.copy2(temp_backup_path, db_path)
            
            # Clean up temporary file
            os.unlink(temp_backup_path)
            
            messages.success(request, 'Database restored successfully!')
            messages.info(request, f'Safety backup created: {safety_backup}')
            
        except Exception as e:
            messages.error(request, f'Restore failed: {str(e)}')
    
    return redirect('pos:database_management')


@login_required
def database_clear(request):
    """Clear specific data from database"""
    if not request.user.is_business_admin and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to clear database data')
        return redirect('pos:database_management')
    
    if request.method == 'POST':
        clear_type = request.POST.get('clear_type')
        
        try:
            if clear_type == 'all':
                # Clear all data using management command
                call_command('db_manager', '--clear-all')
                messages.success(request, 'All data cleared from database successfully!')
                
            elif clear_type == 'products':
                # Clear products for current business only
                call_command('db_manager', '--clear-products', '--business-id', request.business.id)
                messages.success(request, 'Products data cleared successfully!')
                
            elif clear_type == 'sales':
                # Clear sales for current business only
                call_command('db_manager', '--clear-sales', '--business-id', request.business.id)
                messages.success(request, 'Sales data cleared successfully!')
                
            elif clear_type == 'expenses':
                # Clear expenses for current business only
                call_command('db_manager', '--clear-expenses', '--business-id', request.business.id)
                messages.success(request, 'Expenses data cleared successfully!')
                
            else:
                messages.error(request, 'Invalid clear operation specified')
                
        except Exception as e:
            messages.error(request, f'Clear operation failed: {str(e)}')
    
    return redirect('pos:database_management')
