import graphene
from decimal import Decimal
from graphene_django import DjangoObjectType
from products.models import Product
from products.schema.enums.product_enums import SaleTypeEnum


class ProductType(DjangoObjectType):
    """GraphQL type for Product model"""

    # Explicitly define fields that need custom resolvers
    price = graphene.Decimal()
    sale_type = SaleTypeEnum()
    stock = graphene.Int()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "price",
            "unit",
            "sale_type",
            "created_at",
            "updated_at",
        )
        filter_fields = {
            "name": ["exact", "icontains", "istartswith"],
            "sale_type": ["exact"],
            "price": ["exact", "gte", "lte", "gt", "lt"],
            "unit": ["exact", "gte", "lte", "gt", "lt"],
        }
        interfaces = (graphene.relay.Node,)

    def resolve_price(self, info):
        """Resolve product price"""
        return Decimal(str(self.price)) if self.price else Decimal("0.00")

    def resolve_sale_type(self, info):
        """Resolve product sale type to GraphQL enum"""
        # Convert Django TextChoices to string value for GraphQL enum
        return str(self.sale_type) if self.sale_type else None

    def resolve_stock(self, info):
        """Calculate current stock based on latest remaining stock and product unit size"""
        from products.models import StockData

        # Early return if unit is invalid
        if self.unit <= 0:
            return 0

        # Get the latest remaining stock from StockData
        latest_remaining_stock = StockData.get_latest_remaining_stock()

        # Early return if no stock available
        if latest_remaining_stock <= 0:
            return 0

        # Calculate how many units can be made from remaining stock
        # Formula: remaining_stock / (unit * 25L per unit)
        total_litres_needed = self.unit * 25.0

        # Calculate available stock units and return whole number
        return int(latest_remaining_stock / total_litres_needed)
