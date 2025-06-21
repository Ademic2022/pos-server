import graphene
from customers.schema.enums.customer_enums import CustomerTypeEnum, CustomerStatusEnum


class CreateCustomerInput(graphene.InputObjectType):
    """Input type for creating a new customer"""

    name = graphene.String(required=True)
    email = graphene.String()
    phone = graphene.String(required=True)
    address = graphene.String()
    type = CustomerTypeEnum(required=True)
    credit_limit = graphene.Decimal()
    notes = graphene.String()


class UpdateCustomerInput(graphene.InputObjectType):
    """Input type for updating a customer"""

    id = graphene.ID(required=True)
    name = graphene.String()
    email = graphene.String()
    phone = graphene.String()
    address = graphene.String()
    type = CustomerTypeEnum()
    status = CustomerStatusEnum()
    credit_limit = graphene.Decimal()
    notes = graphene.String()


class CustomerFilterInput(graphene.InputObjectType):
    """Input type for filtering customers"""

    search = graphene.String()
    type = CustomerTypeEnum()
    status = CustomerStatusEnum()
    has_balance = graphene.Boolean()
    has_credit_limit = graphene.Boolean()
