import os
import shutil
import sqlite3
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.core.files.storage import default_storage
import tempfile


class Command(BaseCommand):
    help = 'Database management operations: backup, restore, and data deletion'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Create database backup',
        )
        parser.add_argument(
            '--restore',
            type=str,
            help='Restore database from backup file path',
        )
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Clear all data from database',
        )
        parser.add_argument(
            '--clear-products',
            action='store_true',
            help='Clear all products data',
        )
        parser.add_argument(
            '--clear-sales',
            action='store_true',
            help='Clear all sales data',
        )
        parser.add_argument(
            '--clear-expenses',
            action='store_true',
            help='Clear all expenses data',
        )
        parser.add_argument(
            '--business-id',
            type=int,
            help='Specify business ID for business-specific operations',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Output directory for backup files',
        )

    def handle(self, *args, **options):
        business_id = options.get('business_id')
        
        if options['backup']:
            self.create_backup(options.get('output_dir'))
        elif options['restore']:
            self.restore_database(options['restore'])
        elif options['clear_all']:
            self.clear_all_data()
        elif options['clear_products']:
            self.clear_products_data(business_id)
        elif options['clear_sales']:
            self.clear_sales_data(business_id)
        elif options['clear_expenses']:
            self.clear_expenses_data(business_id)
        else:
            self.stdout.write('No operation specified. Use --help for available options.')

    def create_backup(self, output_dir=None):
        """Create a database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if output_dir:
                backup_dir = output_dir
                os.makedirs(backup_dir, exist_ok=True)
            else:
                backup_dir = os.path.join(settings.BASE_DIR, 'backups')
                os.makedirs(backup_dir, exist_ok=True)
            
            backup_filename = f'db_backup_{timestamp}.sqlite3'
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Get database path
            db_path = settings.DATABASES['default']['NAME']
            
            # Copy database file
            shutil.copy2(db_path, backup_path)
            
            self.stdout.write(
                self.style.SUCCESS(f'Backup created successfully: {backup_path}')
            )
            return backup_path
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Backup failed: {str(e)}')
            )
            return None

    def restore_database(self, backup_path):
        """Restore database from backup file"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f'Backup file not found: {backup_path}')
            
            # Get database path
            db_path = settings.DATABASES['default']['NAME']
            
            # Create backup of current database before restore
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safety_backup = os.path.join(
                os.path.dirname(db_path), 
                f'db_before_restore_{timestamp}.sqlite3'
            )
            shutil.copy2(db_path, safety_backup)
            
            # Restore from backup
            shutil.copy2(backup_path, db_path)
            
            self.stdout.write(
                self.style.SUCCESS(f'Database restored successfully from: {backup_path}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Safety backup created: {safety_backup}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Restore failed: {str(e)}')
            )

    def clear_all_data(self):
        """Clear all data from database"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys = OFF;")
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Skip sqlite_sequence table
                tables = [table for table in tables if table != 'sqlite_sequence']
                
                # Clear all tables
                for table in tables:
                    cursor.execute(f"DELETE FROM {table};")
                
                # Reset auto-increment counters
                cursor.execute("DELETE FROM sqlite_sequence;")
                
                cursor.execute("PRAGMA foreign_keys = ON;")
                cursor.execute("VACUUM;")
            
            self.stdout.write(
                self.style.SUCCESS('All data cleared from database successfully')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Clear all data failed: {str(e)}')
            )

    def clear_products_data(self, business_id=None):
        """Clear products and related data"""
        try:
            from pos.models import Product, Category, SaleItem
            
            # Clear sale items first (foreign key constraint)
            if business_id:
                SaleItem.objects.filter(product__business_id=business_id).delete()
                Product.objects.filter(business_id=business_id).delete()
                Category.objects.filter(business_id=business_id).delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Products data cleared for business ID {business_id}')
                )
            else:
                SaleItem.objects.all().delete()
                Product.objects.all().delete()
                Category.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS('All products data cleared successfully')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Clear products data failed: {str(e)}')
            )

    def clear_sales_data(self, business_id=None):
        """Clear sales data"""
        try:
            from pos.models import Sale, SaleItem
            
            if business_id:
                SaleItem.objects.filter(sale__business_id=business_id).delete()
                Sale.objects.filter(business_id=business_id).delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Sales data cleared for business ID {business_id}')
                )
            else:
                SaleItem.objects.all().delete()
                Sale.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS('All sales data cleared successfully')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Clear sales data failed: {str(e)}')
            )

    def clear_expenses_data(self, business_id=None):
        """Clear expenses data"""
        try:
            from pos.models import Expense
            
            if business_id:
                Expense.objects.filter(business_id=business_id).delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Expenses data cleared for business ID {business_id}')
                )
            else:
                Expense.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS('All expenses data cleared successfully')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Clear expenses data failed: {str(e)}')
            )
