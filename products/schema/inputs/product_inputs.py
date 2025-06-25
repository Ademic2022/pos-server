import graphene
from products.schema.enums.product_enums import SaleTypeEnum


class ProductInput(graphene.InputObjectType):
    id = graphene.String(required=True)
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    unit = graphene.Int(required=True)
    sale_type = SaleTypeEnum(required=True)


class UpdateProductInput(graphene.InputObjectType):
    name = graphene.String()
    price = graphene.Decimal()
    unit = graphene.Int()
    sale_type = SaleTypeEnum()
