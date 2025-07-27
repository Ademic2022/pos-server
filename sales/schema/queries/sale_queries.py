"""
GraphQL queries for Sales
"""

from decimal import Decimal
import graphene
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from sales.models import Sale, Payment, CustomerCredit
from sales.schema.enums.sale_enums import SaleTypeEnum, PaymentMethodEnum
from sales.schema.types.sale_types import (
    ReturnType,
    SaleType,
    SaleItemType,
    PaymentType,
    CustomerCreditType,
    SaleStatsType,
    DailySalesType,
)
from sales.models import Return
from sales.schema.filters import (
    SaleFilter,
    SaleItemFilter,
    PaymentFilter,
    CustomerCreditFilter,
)
from shared.types import ValueCountPair


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
        SaleStatsType,
        # Date filters
        date_from=graphene.Date(),
        date_to=graphene.Date(),
        created_at_date=graphene.Date(),
        created_at_month=graphene.Int(),
        created_at_year=graphene.Int(),
        created_at_gte=graphene.DateTime(),
        created_at_lte=graphene.DateTime(),
        # Sale filters
        customer=graphene.ID(),
        sale_type=SaleTypeEnum(),
        transaction_id=graphene.String(),
        transaction_id_icontains=graphene.String(),
        payment_method=PaymentMethodEnum(),
        # Amount filters
        total_gte=graphene.Decimal(),
        total_lte=graphene.Decimal(),
        total_gt=graphene.Decimal(),
        total_lt=graphene.Decimal(),
        subtotal_gte=graphene.Decimal(),
        subtotal_lte=graphene.Decimal(),
        amount_due_gt=graphene.Decimal(),
        amount_due_gte=graphene.Decimal(),
        description="Get sales statistics with comprehensive filtering options",
    )
    daily_sales = graphene.List(
        DailySalesType, date_from=graphene.Date(), date_to=graphene.Date()
    )

    # Recent activities (non-paginated for dashboard widgets)
    recent_sales = graphene.List(SaleType, limit=graphene.Int(default_value=10))
    pending_payments = graphene.List(SaleType)

    # Return queries
    return_request = graphene.Field(
        ReturnType,
        id=graphene.ID(required=True),
        description="Get a single return request by ID",
    )
    returns = graphene.List(
        ReturnType,
        customer_id=graphene.ID(),
        status=graphene.String(),
        sale_id=graphene.ID(),
        limit=graphene.Int(default_value=50),
        description="Get returns with optional filtering",
    )
    pending_returns = graphene.List(
        ReturnType,
        limit=graphene.Int(default_value=20),
        description="Get pending returns for approval",
    )
    customer_returns = graphene.List(
        ReturnType,
        customer_id=graphene.ID(required=True),
        limit=graphene.Int(default_value=20),
        description="Get returns for a specific customer",
    )

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

    def resolve_sales_stats(self, info, **kwargs):
        """Get sales statistics with comprehensive filtering"""
        from customers.models import Customer
        queryset = Sale.objects.all()

        # Extract filter parameters
        date_from = kwargs.get("date_from")
        date_to = kwargs.get("date_to")
        created_at_date = kwargs.get("created_at_date")
        created_at_month = kwargs.get("created_at_month")
        created_at_year = kwargs.get("created_at_year")
        created_at_gte = kwargs.get("created_at_gte")
        created_at_lte = kwargs.get("created_at_lte")
        customer = kwargs.get("customer")
        sale_type = kwargs.get("sale_type")
        transaction_id = kwargs.get("transaction_id")
        transaction_id_icontains = kwargs.get("transaction_id_icontains")
        payment_method = kwargs.get("payment_method")
        total_gte = kwargs.get("total_gte")
        total_lte = kwargs.get("total_lte")
        total_gt = kwargs.get("total_gt")
        total_lt = kwargs.get("total_lt")
        subtotal_gte = kwargs.get("subtotal_gte")
        subtotal_lte = kwargs.get("subtotal_lte")
        amount_due_gt = kwargs.get("amount_due_gt")
        amount_due_gte = kwargs.get("amount_due_gte")

        # Apply date filters
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        if created_at_date:
            queryset = queryset.filter(created_at__date=created_at_date)
        if created_at_month:
            queryset = queryset.filter(created_at__month=created_at_month)
        if created_at_year:
            queryset = queryset.filter(created_at__year=created_at_year)
        if created_at_gte:
            queryset = queryset.filter(created_at__gte=created_at_gte)
        if created_at_lte:
            queryset = queryset.filter(created_at__lte=created_at_lte)

        # Apply sale filters
        if customer:
            queryset = queryset.filter(customer_id=customer)
        if sale_type:
            queryset = queryset.filter(sale_type=sale_type)
        if transaction_id:
            queryset = queryset.filter(transaction_id=transaction_id)
        if transaction_id_icontains:
            queryset = queryset.filter(
                transaction_id__icontains=transaction_id_icontains
            )
        if payment_method:
            queryset = queryset.filter(payments__method=payment_method)

        # Apply amount filters
        if total_gte is not None:
            queryset = queryset.filter(total__gte=total_gte)
        if total_lte is not None:
            queryset = queryset.filter(total__lte=total_lte)
        if total_gt is not None:
            queryset = queryset.filter(total__gt=total_gt)
        if total_lt is not None:
            queryset = queryset.filter(total__lt=total_lt)
        if subtotal_gte is not None:
            queryset = queryset.filter(subtotal__gte=subtotal_gte)
        if subtotal_lte is not None:
            queryset = queryset.filter(subtotal__lte=subtotal_lte)
        if amount_due_gt is not None:
            queryset = queryset.filter(amount_due__gt=amount_due_gt)
        if amount_due_gte is not None:
            queryset = queryset.filter(amount_due__gte=amount_due_gte)

        # Calculate statistics
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
            transfer_sales=Sum("amount", filter=Q(method="transfer")),
            credit_card_sales=Sum("amount", filter=Q(method="credit")),
            part_payment_sales=Sum("amount", filter=Q(method="part_payment")),
        )

        # Get customer credit statistics for the filtered date range
        credit_queryset = CustomerCredit.objects.all()

        # Apply the same date filters to customer credit transactions
        if date_from:
            credit_queryset = credit_queryset.filter(created_at__date__gte=date_from)
        if date_to:
            credit_queryset = credit_queryset.filter(created_at__date__lte=date_to)
        if created_at_date:
            credit_queryset = credit_queryset.filter(created_at__date=created_at_date)
        if created_at_month:
            credit_queryset = credit_queryset.filter(created_at__month=created_at_month)
        if created_at_year:
            credit_queryset = credit_queryset.filter(created_at__year=created_at_year)
        if created_at_gte:
            credit_queryset = credit_queryset.filter(created_at__gte=created_at_gte)
        if created_at_lte:
            credit_queryset = credit_queryset.filter(created_at__lte=created_at_lte)

        # Filter by customer if specified
        if customer:
            credit_queryset = credit_queryset.filter(customer_id=customer)

        customer_credit_stats = credit_queryset.aggregate(
            customer_credit_applied_sum=Sum(
                "amount", filter=Q(transaction_type="credit_used")
            ),
            customer_credit_applied_count=Count(
                "id", filter=Q(transaction_type="credit_used")
            ),
            customer_credit_earned_sum=Sum(
                "amount", filter=Q(transaction_type="credit_earned")
            ),
            customer_credit_earned_count=Count(
                "id", filter=Q(transaction_type="credit_earned")
            ),
        )


        debt_stats = Customer.objects.aggregate(
            total_debt_amount=Sum("balance", filter=Q(balance__lt=0)),
            total_debt_count=Count("balance", filter=Q(balance__lt=0)),
        )

        return SaleStatsType(
            total_sales=stats["total_sales"] or Decimal("0.00"),
            total_transactions=stats["total_transactions"] or 0,
            average_sale_value=round(stats["average_sale_value"] or Decimal("0.00"), 2),
            retail_sales=stats["retail_sales"] or Decimal("0.00"),
            wholesale_sales=stats["wholesale_sales"] or Decimal("0.00"),
            cash_sales=payment_stats["cash_sales"] or Decimal("0.00"),
            transfer_sales=payment_stats["transfer_sales"] or Decimal("0.00"),
            credit_sales=payment_stats["credit_card_sales"] or Decimal("0.00"),
            part_payment_sales=payment_stats["part_payment_sales"] or Decimal("0.00"),
            customer_credit_applied=ValueCountPair(
                value=customer_credit_stats["customer_credit_applied_sum"]
                or Decimal("0.00"),
                count=customer_credit_stats["customer_credit_applied_count"] or 0,
            ),
            customer_credit_earned=ValueCountPair(
                value=customer_credit_stats["customer_credit_earned_sum"]
                or Decimal("0.00"),
                count=customer_credit_stats["customer_credit_earned_count"] or 0,
            ),
            customer_debt_incurred=ValueCountPair(
                value=(
                    abs(debt_stats["total_debt_amount"])
                    if debt_stats["total_debt_amount"]
                    else Decimal("0.00")
                ),
                count=debt_stats["total_debt_count"] or 0,
            ),
            total_discounts=stats["total_discounts"] or Decimal("0.00"),
            # Meta information
            date_range_from=date_from,
            date_range_to=date_to,
            filtered_by_customer=customer,
            filtered_by_sale_type=sale_type,
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
                    "total_sales": Decimal("0"),
                    "total_transactions": 0,
                    "retail_sales": Decimal("0"),
                    "wholesale_sales": Decimal("0"),
                    "cash_payments": Decimal("0"),
                    "transfer_payments": Decimal("0"),
                    "credit_card_payments": Decimal("0"),
                    "part_payment_payments": Decimal("0"),
                    "customer_credit_applied": Decimal("0"),
                    "customer_credit_earned": Decimal("0"),
                    "customer_debt_incurred": Decimal("0"),
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
                    daily_data[date]["credit_card_payments"] += payment.amount
                elif payment.method == "part_payment":
                    daily_data[date]["part_payment_payments"] += payment.amount

            # Add customer credit totals for this sale
            for credit in sale.customercredit_set.all():
                if credit.transaction_type == "credit_used":
                    daily_data[date]["customer_credit_applied"] += credit.amount
                elif credit.transaction_type == "credit_earned":
                    daily_data[date]["customer_credit_earned"] += credit.amount
                elif credit.transaction_type == "debt_incurred":
                    daily_data[date]["customer_debt_incurred"] += credit.amount

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
                credit_card_payments=data["credit_card_payments"],
                part_payment_payments=data["part_payment_payments"],
                customer_credit_applied=data["customer_credit_applied"],
                customer_credit_earned=data["customer_credit_earned"],
                customer_debt_incurred=data["customer_debt_incurred"],
            )
            for date, data in sorted(daily_data.items())
        ]

    def resolve_recent_sales(self, info, limit=10):
        """Get recent sales"""
        return Sale.objects.order_by("-created_at")[:limit]

    def resolve_pending_payments(self, info):
        """Get sales with pending payments (amount_due > 0)"""
        return Sale.objects.filter(amount_due__gt=0).order_by("-created_at")

    # Return resolvers
    def resolve_return_request(self, info, id):
        """Get a single return request by ID"""
        try:
            return Return.objects.get(id=id)
        except Return.DoesNotExist:
            return None

    def resolve_returns(
        self, info, customer_id=None, status=None, sale_id=None, limit=50
    ):
        """Get returns with optional filtering"""
        queryset = Return.objects.all()

        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        if status:
            queryset = queryset.filter(status=status)

        if sale_id:
            queryset = queryset.filter(original_sale_id=sale_id)

        return queryset.order_by("-created_at")[:limit]

    def resolve_pending_returns(self, info, limit=20):
        """Get pending returns for approval"""
        return Return.objects.filter(status="pending").order_by("-created_at")[:limit]

    def resolve_customer_returns(self, info, customer_id, limit=20):
        """Get returns for a specific customer"""
        return Return.objects.filter(customer_id=customer_id).order_by("-created_at")[
            :limit
        ]
