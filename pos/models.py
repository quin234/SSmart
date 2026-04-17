from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from .managers import BusinessFilteredManager


class Business(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    subdomain = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(max_length=50, default='Basic')  # Basic, Pro, Enterprise
    max_users = models.IntegerField(default=5)
    
    # Tax Settings
    enable_tax = models.BooleanField(default=True, help_text="Enable tax calculations")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=16.00, help_text="Tax rate in percentage")
    tax_name = models.CharField(max_length=50, default="VAT", help_text="Name of the tax (e.g., VAT, GST, Sales Tax)")
    
    # Daraja API Settings
    enable_daraja = models.BooleanField(default=False, help_text="Enable Daraja API for M-Pesa payments")
    daraja_consumer_key = models.CharField(max_length=255, blank=True, help_text="Daraja Consumer Key")
    daraja_consumer_secret = models.CharField(max_length=255, blank=True, help_text="Daraja Consumer Secret")
    daraja_passkey = models.CharField(max_length=255, blank=True, help_text="Daraja Pass Key")
    daraja_shortcode = models.CharField(max_length=10, blank=True, help_text="Business Short Code")
    daraja_initiator_name = models.CharField(max_length=100, blank=True, help_text="Initiator Name for transactions")
    daraja_callback_url = models.URLField(blank=True, help_text="Callback URL for M-Pesa transactions")

    class Meta:
        verbose_name_plural = "Businesses"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.subdomain:
            self.subdomain = slugify(self.name)
        super().save(*args, **kwargs)


class User(AbstractUser):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, default='Cashier')  # Admin, Manager, Cashier
    phone = models.CharField(max_length=20, blank=True)
    is_business_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_business = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.business.name if self.business else 'No Business'})"


class Category(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = BusinessFilteredManager()
    all_objects = models.Manager()  # For admin access if needed

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ['business', 'name']

    def __str__(self):
        return f"{self.name} ({self.business.name})"


class Product(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = BusinessFilteredManager()
    all_objects = models.Manager()  # For admin access if needed

    class Meta:
        unique_together = ['business', 'name']
        indexes = [
            models.Index(fields=['business']),
            models.Index(fields=['business', 'name']),
            models.Index(fields=['business', 'barcode']),
            models.Index(fields=['business', 'category']),
            models.Index(fields=['business', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold


class Sale(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('M-Pesa', 'M-Pesa'),
        ('Bank Transfer', 'Bank Transfer'),
    ]

    PAYMENT_STATUS = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
        ('Cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    sale_number = models.CharField(max_length=50, unique=True)
    cashier = models.ForeignKey(User, on_delete=models.CASCADE)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Paid')
    customer_phone = models.CharField(max_length=20, blank=True, help_text="Customer phone number for M-Pesa payments")
    mpesa_transaction_id = models.CharField(max_length=50, blank=True, help_text="M-Pesa transaction ID")
    notes = models.TextField(blank=True)
    sale_date = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=True)
    
    objects = BusinessFilteredManager()
    all_objects = models.Manager()  # For admin access if needed

    class Meta:
        indexes = [
            models.Index(fields=['business']),
            models.Index(fields=['business', 'sale_number']),
            models.Index(fields=['business', 'cashier']),
            models.Index(fields=['business', 'sale_date']),
            models.Index(fields=['business', 'payment_method']),
            models.Index(fields=['business', 'payment_status']),
            models.Index(fields=['mpesa_transaction_id']),
        ]

    def __str__(self):
        return f"Sale {self.sale_number} - {self.business.name}"

    def save(self, *args, **kwargs):
        if not self.sale_number:
            # Generate unique sale number
            last_sale = Sale.objects.filter(business=self.business).order_by('-id').first()
            if last_sale:
                last_number = int(last_sale.sale_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.sale_number = f"{self.business.subdomain.upper()}-{new_number:06d}"
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    objects = BusinessFilteredManager()
    all_objects = models.Manager()  # For admin access if needed

    def __str__(self):
        return f"{self.product.name} x {self.quantity} (Sale {self.sale.sale_number})"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Expense(models.Model):
    EXPENSE_CATEGORIES = [
        ('Rent', 'Rent'),
        ('Utilities', 'Utilities'),
        ('Salaries', 'Salaries'),
        ('Supplies', 'Supplies'),
        ('Marketing', 'Marketing'),
        ('Maintenance', 'Maintenance'),
        ('Insurance', 'Insurance'),
        ('Taxes', 'Taxes'),
        ('Other', 'Other'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, choices=EXPENSE_CATEGORIES)
    expense_date = models.DateField()
    receipt_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = BusinessFilteredManager()
    all_objects = models.Manager()  # For admin access if needed

    def __str__(self):
        return f"{self.description} - {self.business.name}"
