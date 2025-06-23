from django.core.management.base import BaseCommand
from decimal import Decimal
from products.models import StockData


class Command(BaseCommand):
    help = "Add sample stock data for testing"

    def handle(self, *args, **options):
        self.stdout.write("Adding sample stock data...")

        # Sample stock data based on your example
        stock_data = [
            {
                "delivered_quantity": 9200.0,
                "price": Decimal("1.45"),
                "supplier": "Global Oil Ltd",
                "cumulative_stock": 9500.0,  # 300 from previous + 9200 new
                "remaining_stock": 6000.0,  # 9500 - 3500 sold
                "sold_stock": 3500.0,
            },
            {
                "delivered_quantity": 5000.0,
                "price": Decimal("1.42"),
                "supplier": "Fuel Express Co",
                "cumulative_stock": 5000.0,  # First delivery
                "remaining_stock": 4200.0,  # 5000 - 800 sold
                "sold_stock": 800.0,
            },
            {
                "delivered_quantity": 7500.0,
                "price": Decimal("1.48"),
                "supplier": "Metro Petroleum",
                "cumulative_stock": 8100.0,  # 600 from previous + 7500 new
                "remaining_stock": 7300.0,  # 8100 - 800 sold
                "sold_stock": 800.0,
            },
            {
                "delivered_quantity": 3000.0,
                "price": Decimal("1.40"),
                "supplier": "City Fuel Supply",
                "cumulative_stock": 3000.0,  # First delivery
                "remaining_stock": 2100.0,  # 3000 - 900 sold
                "sold_stock": 900.0,
            },
        ]

        created_count = 0
        for data in stock_data:
            stock, created = StockData.objects.get_or_create(
                supplier=data["supplier"],
                delivered_quantity=data["delivered_quantity"],
                defaults=data,
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Created stock delivery: {stock.delivered_quantity:,.0f}L from {stock.supplier}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"- Stock delivery already exists: {stock.delivered_quantity:,.0f}L from {stock.supplier}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted! Created {created_count} new stock records out of {len(stock_data)} total."
            )
        )

        # Display summary statistics
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("STOCK SUMMARY:")
        self.stdout.write("=" * 50)

        all_stock = StockData.objects.all().order_by("-created_at")
        total_delivered = sum(stock.delivered_quantity for stock in all_stock)
        total_cumulative = sum(stock.cumulative_stock for stock in all_stock)
        total_remaining = sum(stock.remaining_stock for stock in all_stock)
        total_sold = sum(stock.sold_stock for stock in all_stock)

        self.stdout.write(f"Total Stock Records: {all_stock.count()}")
        self.stdout.write(f"Total Delivered: {total_delivered:,.0f}L")
        self.stdout.write(f"Total Cumulative Stock: {total_cumulative:,.0f}L")
        self.stdout.write(f"Total Remaining Stock: {total_remaining:,.0f}L")
        self.stdout.write(f"Total Sold Stock: {total_sold:,.0f}L")

        if total_cumulative > 0:
            overall_utilization = (total_sold / total_cumulative) * 100
            self.stdout.write(f"Overall Stock Utilization: {overall_utilization:.1f}%")
