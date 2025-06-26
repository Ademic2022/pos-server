"""
GraphQL types for Sales models
"""

import graphene
from graphene_django import DjangoObjectType
from sales.models import Sale, SaleItem, Payment, CustomerCredit
from sales.schema.enums.sale_enums import (
    SaleTypeEnum,
    PaymentMethodEnum,
    TransactionTypeEnum,
)


class SaleType(DjangoObjectType):
    """GraphQL type for Sale model"""

    # Override sale_type to use enum
    sale_type = SaleTypeEnum()

    class Meta:
        model = Sale
        fields = (
            "id",
            "customer",
            "sale_type",
            "transaction_id",
            "subtotal",
            "discount",
            "total",
            "balance",
            "credit_applied",
            "amount_due",
            "created_at",
            "updated_at",
        )
        # Enable relay-style connections
        interfaces = (graphene.relay.Node,)

    # Add custom fields
    items = graphene.List(lambda: SaleItemType)
    payments = graphene.List(lambda: PaymentType)

    def resolve_sale_type(self, info):
        """Resolve sale type to GraphQL enum"""
        # Convert Django TextChoices to string value for GraphQL enum
        return str(self.sale_type) if self.sale_type else None

    def resolve_items(self, info):
        return self.items.all()

    def resolve_payments(self, info):
        return self.payments.all()


class SaleItemType(DjangoObjectType):
    """GraphQL type for SaleItem model"""

    class Meta:
        model = SaleItem
        fields = ("id", "sale", "product", "quantity", "unit_price", "total_price")
        # Enable relay-style connections
        interfaces = (graphene.relay.Node,)


class PaymentType(DjangoObjectType):
    """GraphQL type for Payment model"""

    # Override method to use enum
    method = PaymentMethodEnum()

    class Meta:
        model = Payment
        fields = ("id", "sale", "method", "amount", "created_at", "updated_at")
        # Enable relay-style connections
        interfaces = (graphene.relay.Node,)

    def resolve_method(self, info):
        """Resolve payment method to GraphQL enum"""
        return str(self.method) if self.method else None


class CustomerCreditType(DjangoObjectType):
    """GraphQL type for CustomerCredit model"""

    # Override transaction_type to use enum
    transaction_type = TransactionTypeEnum()

    class Meta:
        model = CustomerCredit
        fields = (
            "id",
            "customer",
            "transaction_type",
            "amount",
            "balance_after",
            "sale",
            "description",
            "created_at",
            "updated_at",
        )
        # Enable relay-style connections
        interfaces = (graphene.relay.Node,)

    def resolve_transaction_type(self, info):
        """Resolve transaction type to GraphQL enum"""
        return str(self.transaction_type) if self.transaction_type else None


class SaleStatsType(graphene.ObjectType):
    """Statistics for sales"""

    total_sales = graphene.Decimal()
    total_transactions = graphene.Int()
    average_sale_value = graphene.Decimal()
    retail_sales = graphene.Decimal()
    wholesale_sales = graphene.Decimal()
    cash_sales = graphene.Decimal()
    credit_sales = graphene.Decimal()
    total_discounts = graphene.Decimal()


class DailySalesType(graphene.ObjectType):
    """Daily sales summary"""

    date = graphene.Date()
    total_sales = graphene.Decimal()
    total_transactions = graphene.Int()
    retail_sales = graphene.Decimal()
    wholesale_sales = graphene.Decimal()
    cash_payments = graphene.Decimal()
    transfer_payments = graphene.Decimal()
    credit_payments = graphene.Decimal()
