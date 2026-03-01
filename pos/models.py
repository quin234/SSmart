from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify


class Business(models.Model):
    name = models.CharField(max_length=200)
    subdomain = models.SlugField(unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    subscription_plan = models.CharField(max_length=50, default='Basic')  # Basic, Pro, Enterprise
    max_users = models.IntegerField(default=5)

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

    class Meta:
        unique_together = ['business', 'name']

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold


class Sale(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Mobile Money', 'Mobile Money'),
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
    notes = models.TextField(blank=True)
    sale_date = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=True)

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

    def __str__(self):
        return f"{self.description} - {self.business.name}"
