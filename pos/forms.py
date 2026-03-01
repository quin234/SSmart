from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from .models import Business, User, Category, Product, Sale, Expense


class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'email', 'phone', 'address', 'logo', 'subscription_plan', 'max_users']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter your business name',
                'autocomplete': 'organization'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'business@example.com',
                'autocomplete': 'email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '+254 700 000000',
                'autocomplete': 'tel'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 3,
                'placeholder': 'Enter your business address',
                'autocomplete': 'street-address'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control form-control-lg',
                'accept': 'image/*'
            }),
            'subscription_plan': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'max_users': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'min': '1',
                'max': '1000',
                'placeholder': 'Maximum number of users'
            }),
        }


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_business_admin']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_business_admin', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'barcode', 'category', 'buying_price', 'selling_price', 
                 'stock_quantity', 'low_stock_threshold', 'description', 'image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['payment_method', 'payment_status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'amount', 'category', 'expense_date', 'receipt_number', 'notes']
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
