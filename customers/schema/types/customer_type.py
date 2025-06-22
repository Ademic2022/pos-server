import graphene
from decimal import Decimal
from graphene_django import DjangoObjectType
from customers.models import Customer
from customers.schema.enums.customer_enums import CustomerTypeEnum, CustomerStatusEnum


class CustomerType(DjangoObjectType):
    """GraphQL type for Customer model"""

    join_date = graphene.DateTime()
    available_credit = graphene.Decimal()
    is_credit_available = graphene.Boolean()
    type = CustomerTypeEnum()
    status = CustomerStatusEnum()
    balance = graphene.Decimal()

    class Meta:
        model = Customer
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "address",
            "type",
            "status",
            "balance",
            "credit_limit",
            "total_purchases",
            "last_purchase",
            "notes",
            "created_at",
            "updated_at",
        )
        filter_fields = {
            "name": ["exact", "icontains", "istartswith"],
            "email": ["exact", "icontains"],
            "phone": ["exact", "icontains"],
            "address": ["icontains"],
            "type": ["exact"],
            "status": ["exact"],
            "balance": ["exact", "gte", "lte", "gt", "lt"],
        }
        interfaces = (graphene.relay.Node,)

    def resolve_join_date(self, info):
        return self.join_date

    def resolve_available_credit(self, info):
        return self.available_credit

    def resolve_is_credit_available(self, info):
        return self.is_credit_available

    def resolve_type(self, info):
        """Resolve customer type to GraphQL enum"""
        # Convert Django TextChoices to string value for GraphQL enum
        return str(self.type) if self.type else None

    def resolve_status(self, info):
        """Resolve customer status to GraphQL enum"""
        # Convert Django TextChoices to string value for GraphQL enum
        return str(self.status) if self.status else None

    def resolve_balance(self, info):
        """Resolve customer balance"""
        return Decimal(self.balance or "0.00")


class CustomerStatsType(graphene.ObjectType):
    """GraphQL type for customer statistics"""

    total_customers = graphene.Int()
    retail_customers = graphene.Int()
    wholesale_customers = graphene.Int()
    active_customers = graphene.Int()
    inactive_customers = graphene.Int()
    blocked_customers = graphene.Int()
    total_credit_issued = graphene.Decimal()
    total_outstanding_balance = graphene.Decimal()
