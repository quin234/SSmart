from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Business, User, Category, Product, Sale, SaleItem, Expense


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'subdomain', 'email', 'phone', 'is_active', 'subscription_plan', 'created_at']
    list_filter = ['is_active', 'subscription_plan', 'created_at']
    search_fields = ['name', 'subdomain', 'email']
    readonly_fields = ['created_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'business', 'role', 'is_business_admin', 'is_active']
    list_filter = ['role', 'is_business_admin', 'is_active', 'business']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Business Info', {'fields': ('business', 'role', 'phone', 'is_business_admin')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Business Info', {'fields': ('business', 'role', 'phone', 'is_business_admin')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'is_active', 'created_at']
    list_filter = ['is_active', 'business', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'category', 'barcode', 'selling_price', 'stock_quantity', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'business', 'created_at']
    search_fields = ['name', 'barcode', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {'fields': ('business', 'name', 'barcode', 'category')}),
        ('Pricing', {'fields': ('buying_price', 'selling_price')}),
        ('Inventory', {'fields': ('stock_quantity', 'low_stock_threshold')}),
        ('Additional Info', {'fields': ('description', 'image', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['total_price']
    fields = ['product', 'quantity', 'unit_price', 'cost_price', 'total_price']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_number', 'business', 'cashier', 'total_amount', 'payment_method', 'payment_status', 'sale_date']
    list_filter = ['payment_method', 'payment_status', 'business', 'sale_date']
    search_fields = ['sale_number']
    readonly_fields = ['sale_number', 'sale_date']
    inlines = [SaleItemInline]
    
    fieldsets = (
        (None, {'fields': ('business', 'sale_number', 'cashier')}),
        ('Payment', {'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount', 'payment_method', 'payment_status')}),
        ('Additional', {'fields': ('notes', 'is_completed', 'sale_date')}),
    )


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'business', 'category', 'amount', 'expense_date', 'created_by', 'created_at']
    list_filter = ['category', 'business', 'expense_date', 'created_at']
    search_fields = ['description', 'receipt_number', 'notes']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {'fields': ('business', 'description', 'amount', 'category')}),
        ('Details', {'fields': ('expense_date', 'receipt_number', 'notes')}),
        ('System', {'fields': ('created_by', 'created_at')}),
    )
