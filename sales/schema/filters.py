"""
Filters for Sales GraphQL queries
"""

import django_filters
from django_filters import OrderingFilter
from sales.models import Sale, SaleItem, Payment, CustomerCredit


class SaleFilter(django_filters.FilterSet):
    """FilterSet for Sale GraphQL queries with ordering support"""

    # Custom ordering filter
    order_by = OrderingFilter(
        fields=(
            ("id", "id"),
            ("customer", "customer"),
            ("sale_type", "sale_type"),
            ("transaction_id", "transaction_id"),
            ("subtotal", "subtotal"),
            ("discount", "discount"),
            ("total", "total"),
            ("balance", "balance"),
            ("credit_applied", "credit_applied"),
            ("amount_due", "amount_due"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
        ),
    )

    class Meta:
        model = Sale
        fields = {
            "customer": ["exact"],
            "sale_type": ["exact"],
            "transaction_id": ["exact", "icontains"],
            "subtotal": ["exact", "gte", "lte", "gt", "lt"],
            "discount": ["exact", "gte", "lte", "gt", "lt"],
            "total": ["exact", "gte", "lte", "gt", "lt"],
            "balance": ["exact", "gte", "lte", "gt", "lt"],
            "credit_applied": ["exact", "gte", "lte", "gt", "lt"],
            "amount_due": ["exact", "gte", "lte", "gt", "lt"],
            "created_at": ["exact", "date", "month", "year", "gte", "lte"],
            "updated_at": ["exact", "date", "month", "year", "gte", "lte"],
        }


class SaleItemFilter(django_filters.FilterSet):
    """FilterSet for SaleItem GraphQL queries with ordering support"""

    # Custom ordering filter
    order_by = OrderingFilter(
        fields=(
            ("id", "id"),
            ("sale", "sale"),
            ("product", "product"),
            ("quantity", "quantity"),
            ("unit_price", "unit_price"),
            ("total_price", "total_price"),
        ),
    )

    class Meta:
        model = SaleItem
        fields = {
            "sale": ["exact"],
            "product": ["exact"],
            "quantity": ["exact", "gte", "lte", "gt", "lt"],
            "unit_price": ["exact", "gte", "lte", "gt", "lt"],
            "total_price": ["exact", "gte", "lte", "gt", "lt"],
        }


class PaymentFilter(django_filters.FilterSet):
    """FilterSet for Payment GraphQL queries with ordering support"""

    # Custom ordering filter
    order_by = OrderingFilter(
        fields=(
            ("id", "id"),
            ("sale", "sale"),
            ("method", "method"),
            ("amount", "amount"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
        ),
    )

    class Meta:
        model = Payment
        fields = {
            "sale": ["exact"],
            "method": ["exact"],
            "amount": ["exact", "gte", "lte", "gt", "lt"],
            "created_at": ["exact", "date", "month", "year", "gte", "lte"],
            "updated_at": ["exact", "date", "month", "year", "gte", "lte"],
        }


class CustomerCreditFilter(django_filters.FilterSet):
    """FilterSet for CustomerCredit GraphQL queries with ordering support"""

    # Custom ordering filter
    order_by = OrderingFilter(
        fields=(
            ("id", "id"),
            ("customer", "customer"),
            ("transaction_type", "transaction_type"),
            ("amount", "amount"),
            ("balance_after", "balance_after"),
            ("sale", "sale"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
        ),
    )

    class Meta:
        model = CustomerCredit
        fields = {
            "customer": ["exact"],
            "transaction_type": ["exact"],
            "amount": ["exact", "gte", "lte", "gt", "lt"],
            "balance_after": ["exact", "gte", "lte", "gt", "lt"],
            "sale": ["exact"],
            "description": ["icontains"],
            "created_at": ["exact", "date", "month", "year", "gte", "lte"],
            "updated_at": ["exact", "date", "month", "year", "gte", "lte"],
        }
