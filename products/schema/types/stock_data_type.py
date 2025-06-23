import graphene
from graphene_django import DjangoObjectType
from products.models import StockData


class StockDataType(DjangoObjectType):
    """GraphQL type for StockData model"""

    # Add computed fields
    stock_utilization_percentage = graphene.Float()
    previous_remaining_stock = graphene.Float()

    class Meta:
        model = StockData
        interfaces = (graphene.relay.Node,)
        fields = (
            "id",
            "delivered_quantity",
            "price",
            "supplier",
            "cumulative_stock",
            "remaining_stock",
            "sold_stock",
            "created_at",
            "updated_at",
        )

    def resolve_stock_utilization_percentage(self, info):
        """Resolve stock utilization percentage"""
        return self.stock_utilization_percentage

    def resolve_previous_remaining_stock(self, info):
        """Resolve previous remaining stock"""
        return self.previous_remaining_stock
