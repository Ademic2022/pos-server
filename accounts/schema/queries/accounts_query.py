import graphene
from graphene_django.filter import DjangoFilterConnectionField
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from accounts.models import User, Role, ActivityLog
from accounts.schema.types.types import ActivityLogType, RoleType, UserType


class Query(graphene.ObjectType):
    users = DjangoFilterConnectionField(UserType)
    user = graphene.Field(UserType, id=graphene.ID(required=True))
    roles = DjangoFilterConnectionField(RoleType)
    activity_logs = DjangoFilterConnectionField(ActivityLogType)
    current_user = graphene.Field(UserType)

    @method_decorator(login_required)
    def resolve_users(self, info, **kwargs):
        return User.objects.select_related("role").all()

    @method_decorator(login_required)
    def resolve_user(self, info, id):
        try:
            return User.objects.select_related("role").get(pk=id)
        except User.DoesNotExist:
            return None

    @method_decorator(login_required)
    def resolve_roles(self, info, **kwargs):
        return Role.objects.prefetch_related("permissions").all()

    @method_decorator(login_required)
    def resolve_activity_logs(self, info, **kwargs):
        return ActivityLog.objects.select_related("user").all()

    def resolve_current_user(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
