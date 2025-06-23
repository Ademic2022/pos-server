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
        """Calculate current stock - placeholder for inventory logic"""
        # TODO: Implement stock calculation logic
        # This might involve:
        # - Initial inventory
        # - Minus sales
        # - Plus restocks/returns
        return self.unit  # For now, return unit as stock
