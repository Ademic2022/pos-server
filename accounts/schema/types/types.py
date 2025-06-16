import graphene
from graphene_django import DjangoObjectType
from accounts.models import ActivityLog, Role, User


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "last_login",
            "role",
            "phone",
            "address",
            "employee_id",
        )
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "username": ["exact", "icontains"],
            "email": ["exact", "icontains"],
            "is_active": ["exact"],
            "is_staff": ["exact"],
        }


class RoleType(DjangoObjectType):
    class Meta:
        model = Role
        fields = "__all__"
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "name": ["exact", "icontains"],
        }


class ActivityLogType(DjangoObjectType):
    class Meta:
        model = ActivityLog
        fields = "__all__"
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "action": ["exact"],
            "user": ["exact"],
            "timestamp": ["gte", "lte"],
        }
