"""
Django management command to create sample customers
Usage: python manage.py create_sample_customers
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
from customers.models import Customer
from customers.choices import CustomerTypes, StatusChoices


class Command(BaseCommand):
    help = "Create sample customers for the POS system"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing customers before creating new ones",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing customers...")
            Customer.objects.all().delete()

        customers_data = [
            {
                "name": "Adebayo Motors",
                "phone": "08123456789",
                "email": "adebayo@motors.com",
                "address": "Lagos Island, Lagos State",
                "type": "wholesale",
                "balance": 0,
                "credit_limit": 50000,
                "total_purchases": 0,
                "last_purchase": "2025-06-02",
                "created_at": "2024-01-15",
                "status": "active",
                "notes": "Reliable wholesale customer, always pays on time",
            },
            {
                "name": "Mrs. Fatima Ibrahim",
                "phone": "08134567890",
                "email": "",
                "address": "Ikeja, Lagos State",
                "type": "retail",
                "balance": 0,
                "credit_limit": 5000,
                "total_purchases": 0,
                "last_purchase": "2025-06-02",
                "created_at": "2024-03-20",
                "status": "active",
                "notes": "Regular retail customer, prefers cash payments",
            },
            {
                "name": "Kemi's Store",
                "phone": "08145678901",
                "email": "kemi@store.ng",
                "address": "Victoria Island, Lagos State",
                "type": "retail",
                "balance": 0,
                "credit_limit": 5000,
                "total_purchases": 0,
                "last_purchase": "2025-06-02",
                "created_at": "2024-02-10",
                "status": "active",
                "notes": "Good customer but sometimes late on payments",
            },
            {
                "name": "Taiwo Enterprises",
                "phone": "08156789012",
                "email": "taiwo@enterprises.com",
                "address": "Surulere, Lagos State",
                "type": "wholesale",
                "balance": 0,
                "credit_limit": 100000,
                "total_purchases": 0,
                "last_purchase": "2025-06-01",
                "created_at": "2023-11-05",
                "status": "active",
                "notes": "Large wholesale customer, requires extended credit terms",
            },
            {
                "name": "Blessing Oil Depot",
                "phone": "08167890123",
                "email": "blessing@oildepot.ng",
                "address": "Alaba Market, Lagos State",
                "type": "wholesale",
                "balance": 0,
                "credit_limit": 5000,
                "total_purchases": 0,
                "last_purchase": "2025-06-01",
                "created_at": "2024-04-12",
                "status": "active",
                "notes": "New but promising wholesale customer",
            },
            {
                "name": "Chief Okafor",
                "phone": "08178901234",
                "email": "",
                "address": "Mushin, Lagos State",
                "type": "retail",
                "balance": 0,
                "credit_limit": 5000,
                "total_purchases": 0,
                "last_purchase": "2025-05-28",
                "created_at": "2024-06-01",
                "status": "inactive",
                "notes": "Hasn't purchased in a while",
            },
        ]

        self.stdout.write("Creating sample customers...")

        for customer_data in customers_data:
            # Convert date strings to datetime objects
            last_purchase = None
            if customer_data.get("last_purchase"):
                last_purchase = timezone.make_aware(
                    datetime.strptime(customer_data["last_purchase"], "%Y-%m-%d")
                )

            created_at = timezone.make_aware(
                datetime.strptime(customer_data["created_at"], "%Y-%m-%d")
            )

            # Create customer
            customer = Customer.objects.create(
                name=customer_data["name"],
                phone=customer_data["phone"],
                email=customer_data["email"] if customer_data["email"] else None,
                address=customer_data["address"],
                type=customer_data["type"],
                balance=Decimal(str(customer_data["balance"])),
                credit_limit=Decimal(str(customer_data["credit_limit"])),
                total_purchases=Decimal(str(customer_data["total_purchases"])),
                last_purchase=last_purchase,
                status=customer_data["status"],
                notes=customer_data["notes"],
                created_at=created_at,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created customer: {customer.name} ({customer.type})"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {len(customers_data)} customers")
        )
