from django.core.management.base import BaseCommand
from products.models import Product
from products.choices import SaleType
from decimal import Decimal


class Command(BaseCommand):
    help = "Populate products from TypeScript data"

    def handle(self, *args, **options):
        # Wholesale products
        wholesale_products = [
            {
                "name": "Wholesale Drum (9 Kegs)",
                "price": "396000.00",
                "unit": 9,
                "sale_type": SaleType.WHOLESALE,
            }
        ]

        # Retail products
        retail_products = [
            {"name": "Single Keg", "price": "45000.00", "unit": 1},
            {"name": "2 Kegs", "price": "90000.00", "unit": 2},
            {"name": "3 Kegs", "price": "128000.00", "unit": 3},
            {"name": "4 Kegs", "price": "173000.00", "unit": 4},
            {"name": "5 Kegs", "price": "216000.00", "unit": 5},
            {"name": "6 Kegs", "price": "261000.00", "unit": 6},
            {"name": "7 Kegs", "price": "305000.00", "unit": 7},
            {"name": "8 Kegs", "price": "349000.00", "unit": 8},
        ]

        # Add sale_type to retail products
        for product in retail_products:
            product["sale_type"] = SaleType.RETAIL

        # Combine all products
        all_products = wholesale_products + retail_products

        # Clear existing products first (optional - remove this line if you want to keep existing)
        self.stdout.write("🗑️  Clearing existing products...")
        Product.objects.all().delete()

        # Create products
        created_count = 0

        for product_data in all_products:
            # Convert price to Decimal for consistency
            product_data["price"] = Decimal(str(product_data["price"]))

            # Create product (Django auto-generates ID)
            product = Product.objects.create(**product_data)
            created_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Created product: {product.name} (ID: {product.id})"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Successfully processed {len(all_products)} products:"
                f"\n   - Created: {created_count} products"
            )
        )
