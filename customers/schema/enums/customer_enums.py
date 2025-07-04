import graphene
from customers.choices import CustomerTypes, StatusChoices


class CustomerTypeEnum(graphene.Enum):

    class Meta:
        enum = CustomerTypes


class CustomerStatusEnum(graphene.Enum):
    class Meta:
        enum = StatusChoices
