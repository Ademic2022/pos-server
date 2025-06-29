import graphene
from graphene_django.filter import DjangoFilterConnectionField
from products.schema.types.stock_data_type import StockDataType
from products.schema.filters import StockDataFilter
from products.models import StockData


class Query(graphene.ObjectType):
    """GraphQL queries for StockData"""

    # Single stock data query
    stock_data = graphene.Field(StockDataType, id=graphene.ID())

    # Multiple stock data query with filtering
    all_stock_data = DjangoFilterConnectionField(
        StockDataType, filterset_class=StockDataFilter
    )

    # Custom queries
    stock_data_by_supplier = graphene.List(
        StockDataType, supplier=graphene.String(required=True)
    )

    latest_stock_deliveries = graphene.List(
        StockDataType, limit=graphene.Int(default_value=10)
    )

    def resolve_stock_data(self, info, id):
        """Resolve single stock data by ID"""
        try:
            return StockData.objects.get(pk=id)
        except StockData.DoesNotExist:
            return None

    def resolve_stock_data_by_supplier(self, info, supplier):
        """Resolve stock data by supplier"""
        return StockData.objects.filter(supplier__icontains=supplier).order_by(
            "-created_at"
        )

    def resolve_latest_stock_deliveries(self, info, limit):
        """Resolve latest stock deliveries"""
        return StockData.objects.all().order_by("-created_at")[:limit]
