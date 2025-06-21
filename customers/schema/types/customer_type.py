import graphene
from graphene_django import DjangoObjectType
from customers.models import Customer
from customers.choices import CustomerTypes, StatusChoices

# Create GraphQL Enums from Django choices
CustomerTypeEnum = graphene.Enum.from_enum(CustomerTypes)
StatusChoiceEnum = graphene.Enum.from_enum(StatusChoices)


class CustomerType(DjangoObjectType):
    """GraphQL type for Customer model"""

    join_date = graphene.DateTime()
    available_credit = graphene.Decimal()
    is_credit_available = graphene.Boolean()
    type = CustomerTypeEnum()
    status = StatusChoiceEnum()

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
