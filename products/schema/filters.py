import django_filters
from products.models import StockData


class StockDataFilter(django_filters.FilterSet):
    """FilterSet for StockData GraphQL queries"""

    # Filter by supplier (case-insensitive)
    supplier = django_filters.CharFilter(lookup_expr="icontains")

    # Filter by price range
    price__gte = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price__lte = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    # Filter by stock quantities
    remaining_stock__gte = django_filters.NumberFilter(
        field_name="remaining_stock", lookup_expr="gte"
    )
    remaining_stock__lte = django_filters.NumberFilter(
        field_name="remaining_stock", lookup_expr="lte"
    )

    delivered_quantity__gte = django_filters.NumberFilter(
        field_name="delivered_quantity", lookup_expr="gte"
    )
    delivered_quantity__lte = django_filters.NumberFilter(
        field_name="delivered_quantity", lookup_expr="lte"
    )

    # Filter by date range
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = StockData
        fields = [
            "supplier",
            "price",
            "remaining_stock",
            "delivered_quantity",
            "cumulative_stock",
            "sold_stock",
            "created_at",
            "updated_at",
        ]
