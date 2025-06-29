from decimal import Decimal
import graphene
from django.db.models import Q, Sum, Count
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import login_required
from customers.models import Customer
from customers.schema.types.customer_type import CustomerType, CustomerStatsType


class Query(graphene.ObjectType):
    """GraphQL queries for customers"""

    # Single customer queries
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))

    # Multiple customer queries with filtering and pagination
    customers = DjangoFilterConnectionField(CustomerType)

    # Statistics
    customer_stats = graphene.Field(CustomerStatsType)

    @login_required
    def resolve_customer(self, info, id):
        """Get a single customer by ID"""
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None

    @login_required
    def resolve_customers(self, info, **kwargs):
        """Get multiple customers with filtering and pagination"""
        return Customer.objects.select_related().all()

    @login_required
    def resolve_customer_stats(self, info):
        """Get customer statistics"""
        stats = Customer.objects.aggregate(
            total_customers=Count("id"),
            retail_customers=Count("id", filter=Q(type="retail")),
            wholesale_customers=Count("id", filter=Q(type="wholesale")),
            active_customers=Count("id", filter=Q(status="active")),
            inactive_customers=Count("id", filter=Q(status="inactive")),
            blocked_customers=Count("id", filter=Q(status="blocked")),
            total_credit_issued=Sum("credit_limit"),
            total_outstanding_balance=Sum("balance"),
        )

        return CustomerStatsType(
            total_customers=stats["total_customers"] or Decimal("0.00"),
            retail_customers=stats["retail_customers"] or Decimal("0.00"),
            wholesale_customers=stats["wholesale_customers"] or Decimal("0.00"),
            active_customers=stats["active_customers"] or Decimal("0.00"),
            inactive_customers=stats["inactive_customers"] or Decimal("0.00"),
            blocked_customers=stats["blocked_customers"] or Decimal("0.00"),
            total_credit_issued=stats["total_credit_issued"] or Decimal("0.00"),
            total_outstanding_balance=stats["total_outstanding_balance"]
            or Decimal("0.00"),
        )
