"""
GraphQL input types for Sales mutations
"""
import graphene
from sales.schema.enums.sale_enums import SaleTypeEnum, PaymentMethodEnum, TransactionTypeEnum


class SaleItemInput(graphene.InputObjectType):
    """Input type for sale items"""
    product_id = graphene.ID(required=True)
    quantity = graphene.Int(required=True)
    unit_price = graphene.Decimal(required=True)


class PaymentInput(graphene.InputObjectType):
    """Input type for payments"""
    method = PaymentMethodEnum(required=True)
    amount = graphene.Decimal(required=True)


class CreateSaleInput(graphene.InputObjectType):
    """Input type for creating a sale"""
    customer_id = graphene.ID()
    sale_type = SaleTypeEnum(required=True, default_value=SaleTypeEnum.RETAIL)
    items = graphene.List(SaleItemInput, required=True)
    payments = graphene.List(PaymentInput, required=True)
    discount = graphene.Decimal(default_value=0)
    credit_applied = graphene.Decimal(default_value=0)


class UpdateSaleInput(graphene.InputObjectType):
    """Input type for updating a sale"""
    sale_id = graphene.ID(required=True)
    customer_id = graphene.ID()
    discount = graphene.Decimal()
    credit_applied = graphene.Decimal()


class AddPaymentInput(graphene.InputObjectType):
    """Input type for adding payment to a sale"""
    sale_id = graphene.ID(required=True)
    method = PaymentMethodEnum(required=True)
    amount = graphene.Decimal(required=True)


class CustomerCreditInput(graphene.InputObjectType):
    """Input type for customer credit transactions"""
    customer_id = graphene.ID(required=True)
    transaction_type = TransactionTypeEnum(required=True)
    amount = graphene.Decimal(required=True)
    description = graphene.String()
    sale_id = graphene.ID()
