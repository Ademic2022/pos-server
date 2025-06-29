"""
GraphQL queries for Sales
"""

from decimal import Decimal
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from sales.models import Sale, Payment, CustomerCredit
from sales.filters import (
    SaleFilter,
    SaleItemFilter,
    PaymentFilter,
    CustomerCreditFilter,
)
from sales.schema.types.sale_types import (
    SaleType,
    SaleItemType,
    PaymentType,
    CustomerCreditType,
    SaleStatsType,
    DailySalesType,
)


class Query(graphene.ObjectType):
    """Sales queries using DjangoFilterConnectionField"""

    # Connection fields with filtering and pagination
    sales = DjangoFilterConnectionField(
        SaleType,
        filterset_class=SaleFilter,
        description="Get sales with filtering and pagination",
    )
    sale_items = DjangoFilterConnectionField(
        SaleItemType,
        filterset_class=SaleItemFilter,
        description="Get sale items with filtering and pagination",
    )
    payments = DjangoFilterConnectionField(
        PaymentType,
        filterset_class=PaymentFilter,
        description="Get payments with filtering and pagination",
    )
    customer_credits = DjangoFilterConnectionField(
        CustomerCreditType,
        filterset_class=CustomerCreditFilter,
        description="Get customer credits with filtering and pagination",
    )

    # Individual record queries
    sale = graphene.Field(SaleType, id=graphene.ID(required=True))

    # Customer credit balance
    customer_credit_balance = graphene.Decimal(customer_id=graphene.ID(required=True))

    # Statistics and reports
    sales_stats = graphene.Field(
        SaleStatsType, date_from=graphene.Date(), date_to=graphene.Date()
    )
    daily_sales = graphene.List(
        DailySalesType, date_from=graphene.Date(), date_to=graphene.Date()
    )

    # Recent activities (non-paginated for dashboard widgets)
    recent_sales = graphene.List(SaleType, limit=graphene.Int(default_value=10))
    pending_payments = graphene.List(SaleType)

    def resolve_sale(self, info, id):
        """Get a single sale by ID"""
        try:
            return Sale.objects.get(id=id)
        except Sale.DoesNotExist:
            return None

    def resolve_customer_credit_balance(self, info, customer_id):
        """Get current customer credit balance"""
        latest_credit = (
            CustomerCredit.objects.filter(customer_id=customer_id)
            .order_by("-created_at")
            .first()
        )

        return latest_credit.balance_after if latest_credit else 0

    def resolve_sales_stats(self, info, date_from=None, date_to=None):
        """Get sales statistics"""
        queryset = Sale.objects.all()

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        stats = queryset.aggregate(
            total_sales=Sum("total"),
            total_transactions=Count("id"),
            average_sale_value=Avg("total"),
            retail_sales=Sum("total", filter=Q(sale_type="retail")),
            wholesale_sales=Sum("total", filter=Q(sale_type="wholesale")),
            total_discounts=Sum("discount"),
        )

        # Get payment method totals
        payment_stats = Payment.objects.filter(sale__in=queryset).aggregate(
            cash_sales=Sum("amount", filter=Q(method="cash")),
            credit_sales=Sum("amount", filter=Q(method="credit")),
        )

        return SaleStatsType(
            total_sales=stats["total_sales"] or Decimal("0.00"),
            total_transactions=stats["total_transactions"] or Decimal("0.00"),
            average_sale_value=stats["average_sale_value"] or Decimal("0.00"),
            retail_sales=stats["retail_sales"] or Decimal("0.00"),
            wholesale_sales=stats["wholesale_sales"] or Decimal("0.00"),
            cash_sales=payment_stats["cash_sales"] or Decimal("0.00"),
            credit_sales=payment_stats["credit_sales"] or Decimal("0.00"),
            total_discounts=stats["total_discounts"] or Decimal("0.00"),
        )

    def resolve_daily_sales(self, info, date_from=None, date_to=None):
        """Get daily sales summary"""
        queryset = Sale.objects.all()

        if not date_from:
            date_from = timezone.now().date() - timedelta(days=30)

        if not date_to:
            date_to = timezone.now().date()

        queryset = queryset.filter(
            created_at__date__gte=date_from, created_at__date__lte=date_to
        )

        # Group by date and calculate daily totals
        daily_data = {}

        for sale in queryset:
            date = sale.created_at.date()

            if date not in daily_data:
                daily_data[date] = {
                    "total_sales": 0,
                    "total_transactions": 0,
                    "retail_sales": 0,
                    "wholesale_sales": 0,
                    "cash_payments": 0,
                    "transfer_payments": 0,
                    "credit_payments": 0,
                }

            daily_data[date]["total_sales"] += sale.total
            daily_data[date]["total_transactions"] += 1

            if sale.sale_type == "retail":
                daily_data[date]["retail_sales"] += sale.total
            else:
                daily_data[date]["wholesale_sales"] += sale.total

            # Add payment method totals
            for payment in sale.payments.all():
                if payment.method == "cash":
                    daily_data[date]["cash_payments"] += payment.amount
                elif payment.method == "transfer":
                    daily_data[date]["transfer_payments"] += payment.amount
                elif payment.method == "credit":
                    daily_data[date]["credit_payments"] += payment.amount

        # Convert to list of DailySalesType
        return [
            DailySalesType(
                date=date,
                total_sales=data["total_sales"],
                total_transactions=data["total_transactions"],
                retail_sales=data["retail_sales"],
                wholesale_sales=data["wholesale_sales"],
                cash_payments=data["cash_payments"],
                transfer_payments=data["transfer_payments"],
                credit_payments=data["credit_payments"],
            )
            for date, data in sorted(daily_data.items())
        ]

    def resolve_recent_sales(self, info, limit=10):
        """Get recent sales"""
        return Sale.objects.order_by("-created_at")[:limit]

    def resolve_pending_payments(self, info):
        """Get sales with pending payments (amount_due > 0)"""
        return Sale.objects.filter(amount_due__gt=0).order_by("-created_at")
