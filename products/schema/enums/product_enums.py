import graphene


class SaleTypeEnum(graphene.Enum):
    WHOLESALE = "wholesale"
    RETAIL = "retail"
