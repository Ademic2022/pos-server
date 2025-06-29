import graphene
from products.models import Product
from products.schema.types.product_type import ProductType
from graphene_django.filter import DjangoFilterConnectionField


class Query(graphene.ObjectType):
    # Get all products with filtering and pagination
    products = DjangoFilterConnectionField(ProductType)

    # Get single product
    product = graphene.Field(
        ProductType,
        id=graphene.ID(required=True),
        description="Get a single product by ID",
    )

    def resolve_product(self, info, id):
        """Resolve single product by ID"""
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None
