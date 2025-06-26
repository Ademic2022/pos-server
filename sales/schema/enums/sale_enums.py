"""
GraphQL enums for Sales models
"""
import graphene
from sales.choices import SaleTypeChoices, PaymentMethodChoices, TransactionTypeChoices


class SaleTypeEnum(graphene.Enum):
    """GraphQL enum for sale types"""
    RETAIL = SaleTypeChoices.RETAIL.value
    WHOLESALE = SaleTypeChoices.WHOLESALE.value


class PaymentMethodEnum(graphene.Enum):
    """GraphQL enum for payment methods"""
    CASH = PaymentMethodChoices.CASH.value
    TRANSFER = PaymentMethodChoices.TRANSFER.value
    CREDIT = PaymentMethodChoices.CREDIT.value
    PART_PAYMENT = PaymentMethodChoices.PART_PAYMENT.value


class TransactionTypeEnum(graphene.Enum):
    """GraphQL enum for transaction types"""
    CREDIT_ADDED = TransactionTypeChoices.CREDIT_ADDED.value
    CREDIT_USED = TransactionTypeChoices.CREDIT_USED.value
    CREDIT_REFUND = TransactionTypeChoices.CREDIT_REFUND.value
