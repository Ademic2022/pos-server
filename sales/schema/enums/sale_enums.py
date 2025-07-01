"""
GraphQL enums for Sales models
"""

import graphene
from sales.choices import SaleTypeChoices, PaymentMethodChoices, TransactionTypeChoices


class SaleTypeEnum(graphene.Enum):
    """GraphQL enum for sale types"""

    class Meta:
        enum = SaleTypeChoices


class PaymentMethodEnum(graphene.Enum):
    """GraphQL enum for payment methods"""

    class Meta:
        enum = PaymentMethodChoices


class TransactionTypeEnum(graphene.Enum):
    """GraphQL enum for transaction types"""

    class Meta:
        enum = TransactionTypeChoices
