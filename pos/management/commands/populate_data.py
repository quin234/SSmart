from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from pos.models import Business, User, Category, Product, Sale, SaleItem, Expense
import random
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Populate the database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample businesses
        business1 = Business.objects.create(
            name="Tech Store Plus",
            subdomain="techstore",
            email="info@techstore.com",
            phone="+1234567890",
            address="123 Tech Street, Silicon Valley, CA 94000",
            subscription_plan="Pro"
        )
        
        business2 = Business.objects.create(
            name="Fashion Boutique",
            subdomain="fashion",
            email="contact@fashionboutique.com",
            phone="+1987654321",
            address="456 Fashion Ave, New York, NY 10001",
            subscription_plan="Basic"
        )
        
        # Create users for each business
        # Business 1 users
        admin_user1 = User.objects.create_user(
            username="tech_admin",
            email="admin@techstore.com",
            password="admin123",
            first_name="John",
            last_name="Doe",
            business=business1,
            role="Admin",
            phone="+1234567890",
            is_business_admin=True
        )
        
        manager_user1 = User.objects.create_user(
            username="tech_manager",
            email="manager@techstore.com",
            password="manager123",
            first_name="Jane",
            last_name="Smith",
            business=business1,
            role="Manager",
            phone="+1234567891"
        )
        
        cashier_user1 = User.objects.create_user(
            username="tech_cashier",
            email="cashier@techstore.com",
            password="cashier123",
            first_name="Mike",
            last_name="Johnson",
            business=business1,
            role="Cashier",
            phone="+1234567892"
        )
        
        # Business 2 users
        admin_user2 = User.objects.create_user(
            username="fashion_admin",
            email="admin@fashion.com",
            password="admin123",
            first_name="Sarah",
            last_name="Wilson",
            business=business2,
            role="Admin",
            phone="+1987654321",
            is_business_admin=True
        )
        
        cashier_user2 = User.objects.create_user(
            username="fashion_cashier",
            email="cashier@fashion.com",
            password="cashier123",
            first_name="Emma",
            last_name="Brown",
            business=business2,
            role="Cashier",
            phone="+1987654322"
        )
        
        # Create categories for Tech Store
        tech_categories = [
            {"name": "Laptops", "description": "Laptop computers and accessories"},
            {"name": "Smartphones", "description": "Mobile phones and accessories"},
            {"name": "Tablets", "description": "Tablet devices"},
            {"name": "Accessories", "description": "Computer accessories and peripherals"},
            {"name": "Software", "description": "Software licenses and digital products"},
        ]
        
        for cat_data in tech_categories:
            Category.objects.create(
                business=business1,
                name=cat_data["name"],
                description=cat_data["description"]
            )
        
        # Create categories for Fashion Boutique
        fashion_categories = [
            {"name": "Women's Clothing", "description": "Clothing for women"},
            {"name": "Men's Clothing", "description": "Clothing for men"},
            {"name": "Shoes", "description": "Footwear for all"},
            {"name": "Accessories", "description": "Fashion accessories"},
            {"name": "Bags", "description": "Handbags and backpacks"},
        ]
        
        for cat_data in fashion_categories:
            Category.objects.create(
                business=business2,
                name=cat_data["name"],
                description=cat_data["description"]
            )
        
        # Create products for Tech Store
        tech_products = [
            {"name": "Laptop Pro 15", "barcode": "LP001", "category": "Laptops", "buying": 800, "selling": 1200, "stock": 25},
            {"name": "Smartphone X", "barcode": "SP001", "category": "Smartphones", "buying": 400, "selling": 650, "stock": 50},
            {"name": "Tablet Plus", "barcode": "TB001", "category": "Tablets", "buying": 250, "selling": 400, "stock": 30},
            {"name": "Wireless Mouse", "barcode": "WM001", "category": "Accessories", "buying": 15, "selling": 35, "stock": 100},
            {"name": "USB Keyboard", "barcode": "KB001", "category": "Accessories", "buying": 25, "selling": 50, "stock": 75},
            {"name": "Office Suite", "barcode": "SW001", "category": "Software", "buying": 50, "selling": 150, "stock": 200},
            {"name": "Gaming Laptop", "barcode": "GL001", "category": "Laptops", "buying": 1200, "selling": 1800, "stock": 15},
            {"name": "Budget Phone", "barcode": "BP001", "category": "Smartphones", "buying": 100, "selling": 200, "stock": 80},
        ]
        
        for prod_data in tech_products:
            category = Category.objects.get(business=business1, name=prod_data["category"])
            Product.objects.create(
                business=business1,
                name=prod_data["name"],
                barcode=prod_data["barcode"],
                category=category,
                buying_price=Decimal(str(prod_data["buying"])),
                selling_price=Decimal(str(prod_data["selling"])),
                stock_quantity=prod_data["stock"],
                low_stock_threshold=10
            )
        
        # Create products for Fashion Boutique
        fashion_products = [
            {"name": "Summer Dress", "barcode": "FD001", "category": "Women's Clothing", "buying": 30, "selling": 75, "stock": 40},
            {"name": "Men's Shirt", "barcode": "MS001", "category": "Men's Clothing", "buying": 25, "selling": 60, "stock": 60},
            {"name": "Running Shoes", "barcode": "RS001", "category": "Shoes", "buying": 40, "selling": 90, "stock": 35},
            {"name": "Handbag Premium", "barcode": "HB001", "category": "Bags", "buying": 50, "selling": 150, "stock": 20},
            {"name": "Fashion Scarf", "barcode": "FS001", "category": "Accessories", "buying": 10, "selling": 30, "stock": 100},
            {"name": "Winter Jacket", "barcode": "WJ001", "category": "Women's Clothing", "buying": 60, "selling": 140, "stock": 25},
            {"name": "Men's Jeans", "barcode": "MJ001", "category": "Men's Clothing", "buying": 35, "selling": 80, "stock": 45},
            {"name": "Sports Shoes", "barcode": "SS001", "category": "Shoes", "buying": 45, "selling": 95, "stock": 30},
        ]
        
        for prod_data in fashion_products:
            category = Category.objects.get(business=business2, name=prod_data["category"])
            Product.objects.create(
                business=business2,
                name=prod_data["name"],
                barcode=prod_data["barcode"],
                category=category,
                buying_price=Decimal(str(prod_data["buying"])),
                selling_price=Decimal(str(prod_data["selling"])),
                stock_quantity=prod_data["stock"],
                low_stock_threshold=15
            )
        
        # Create sample sales for Tech Store
        self.create_sample_sales(business1, [admin_user1, manager_user1, cashier_user1])
        
        # Create sample sales for Fashion Boutique
        self.create_sample_sales(business2, [admin_user2, cashier_user2])
        
        # Create sample expenses
        self.create_sample_expenses(business1, admin_user1)
        self.create_sample_expenses(business2, admin_user2)
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('Tech Store Admin: tech_admin / admin123')
        self.stdout.write('Tech Store Manager: tech_manager / manager123')
        self.stdout.write('Tech Store Cashier: tech_cashier / cashier123')
        self.stdout.write('Fashion Admin: fashion_admin / admin123')
        self.stdout.write('Fashion Cashier: fashion_cashier / cashier123')
        self.stdout.write('Super Admin: admin / admin123')
    
    def create_sample_sales(self, business, users):
        products = list(Product.objects.filter(business=business))
        
        for i in range(20):  # Create 20 sample sales
            cashier = random.choice(users)
            sale = Sale.objects.create(
                business=business,
                cashier=cashier,
                subtotal=Decimal('0'),
                tax_amount=Decimal('0'),
                discount_amount=Decimal(random.choice([0, 5, 10, 20])),
                total_amount=Decimal('0'),
                payment_method=random.choice(['Cash', 'Card', 'Mobile Money']),
                payment_status='Paid',
                sale_date=timezone.now() - timedelta(days=random.randint(0, 30))
            )
            
            # Add 1-5 random products to the sale
            num_items = random.randint(1, min(5, len(products)))
            selected_products = random.sample(products, num_items)
            
            subtotal = Decimal('0')
            for product in selected_products:
                quantity = random.randint(1, 3)
                unit_price = product.selling_price
                total_price = unit_price * quantity
                
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    cost_price=product.buying_price
                )
                
                subtotal += total_price
            
            # Calculate totals
            tax_amount = subtotal * Decimal('0.1')  # 10% tax
            total_amount = subtotal + tax_amount - sale.discount_amount
            
            sale.subtotal = subtotal
            sale.tax_amount = tax_amount
            sale.total_amount = total_amount
            sale.save()
    
    def create_sample_expenses(self, business, user):
        expense_categories = ['Rent', 'Utilities', 'Salaries', 'Supplies', 'Marketing', 'Maintenance']
        
        for category in expense_categories:
            Expense.objects.create(
                business=business,
                description=f"{category} - {timezone.now().strftime('%B %Y')}",
                amount=Decimal(random.randint(500, 5000)),
                category=category,
                expense_date=timezone.now().date() - timedelta(days=random.randint(0, 30)),
                receipt_number=f"REC{random.randint(1000, 9999)}",
                created_by=user
            )
