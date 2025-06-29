import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import login_required
from accounts.models import User, Role, ActivityLog
from accounts.schema.types.types import ActivityLogType, RoleType, UserNode


class Query(graphene.ObjectType):
    users = DjangoFilterConnectionField(UserNode)
    user = graphene.Field(UserNode, id=graphene.ID(required=True))
    roles = DjangoFilterConnectionField(RoleType)
    activity_logs = DjangoFilterConnectionField(ActivityLogType)
    view_me = graphene.Field(UserNode)

    @login_required
    def resolve_users(self, info, **kwargs):
        user = info.context.user
        if not user.is_staff:
            raise PermissionError("You must be staff to access this resource")
        return User.objects.select_related("role").all()

    @login_required
    def resolve_user(self, info, id):
        user = info.context.user

        # Allow users to query themselves, or require staff for other users
        if str(user.id) != str(id) and not user.is_staff:
            raise PermissionError("You must be staff to access other users")

        try:
            return User.objects.select_related("role").get(pk=id)
        except User.DoesNotExist:
            return None

    @login_required
    def resolve_roles(self, info, **kwargs):
        user = info.context.user
        if not user.is_staff:
            raise PermissionError("You must be staff to access this resource")
        return Role.objects.prefetch_related("permissions").all()

    @login_required
    def resolve_activity_logs(self, info, **kwargs):
        user = info.context.user
        if not user.is_staff:
            raise PermissionError("You must be staff to access this resource")
        return ActivityLog.objects.select_related("user").all()

    def resolve_view_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
