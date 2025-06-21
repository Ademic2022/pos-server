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
        return User.objects.select_related("role").all()

    @login_required
    def resolve_user(self, info, id):
        try:
            return User.objects.select_related("role").get(pk=id)
        except User.DoesNotExist:
            return None

    @login_required
    def resolve_roles(self, info, **kwargs):
        return Role.objects.prefetch_related("permissions").all()

    @login_required
    def resolve_activity_logs(self, info, **kwargs):
        return ActivityLog.objects.select_related("user").all()

    def resolve_view_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
