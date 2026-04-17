from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from .models import Business, User, Category, Product, Sale, Expense


class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'email', 'phone', 'address', 'subscription_plan', 'max_users']
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
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter category description (optional)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'barcode', 'category', 'buying_price', 'selling_price', 
                 'stock_quantity', 'low_stock_threshold', 'description', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter barcode (optional)'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'buying_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', 'min': '0'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter product description (optional)'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['payment_method', 'payment_status', 'notes']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes (optional)'}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['description', 'amount', 'category', 'expense_date', 'receipt_number', 'notes']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter expense description'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'receipt_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter receipt number (optional)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes (optional)'}),
        }


class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['enable_tax', 'tax_rate', 'tax_name', 'enable_daraja', 'daraja_consumer_key', 
                  'daraja_consumer_secret', 'daraja_passkey', 'daraja_shortcode', 
                  'daraja_initiator_name', 'daraja_callback_url']
        widgets = {
            'enable_tax': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'data-bs-toggle': 'toggle'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'tax_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., VAT, GST, Sales Tax'
            }),
            'enable_daraja': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'data-bs-toggle': 'toggle'
            }),
            'daraja_consumer_key': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Daraja Consumer Key'
            }),
            'daraja_consumer_secret': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Daraja Consumer Secret'
            }),
            'daraja_passkey': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Daraja Pass Key'
            }),
            'daraja_shortcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 174379'
            }),
            'daraja_initiator_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., BUSINESSAPI'
            }),
            'daraja_callback_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourdomain.com/callback'
            })
        }
        labels = {
            'enable_tax': 'Enable Tax Calculations',
            'tax_rate': 'Tax Rate (%)',
            'tax_name': 'Tax Name',
            'enable_daraja': 'Enable Daraja API (M-Pesa)',
            'daraja_consumer_key': 'Consumer Key',
            'daraja_consumer_secret': 'Consumer Secret',
            'daraja_passkey': 'Pass Key',
            'daraja_shortcode': 'Business Short Code',
            'daraja_initiator_name': 'Initiator Name',
            'daraja_callback_url': 'Callback URL'
        }
        help_texts = {
            'enable_tax': 'Turn on to include tax calculations in sales',
            'tax_rate': 'Enter the tax percentage (e.g., 16.00 for 16%)',
            'tax_name': 'Name that will appear on receipts and invoices',
            'enable_daraja': 'Enable M-Pesa payments using Daraja API',
            'daraja_consumer_key': 'Get this from your Daraja developer account',
            'daraja_consumer_secret': 'Keep this secret and secure',
            'daraja_passkey': 'Used for authenticating API requests',
            'daraja_shortcode': 'Your business M-Pesa short code',
            'daraja_initiator_name': 'Name used to initiate transactions',
            'daraja_callback_url': 'URL where M-Pesa will send payment confirmations'
        }
