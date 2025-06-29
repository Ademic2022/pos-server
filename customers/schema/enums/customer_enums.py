import graphene


class CustomerTypeEnum(graphene.Enum):
    RETAIL = "retail"
    WHOLESALE = "wholesale"


class CustomerStatusEnum(graphene.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
