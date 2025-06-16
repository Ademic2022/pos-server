import graphene
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from accounts.models import ActivityLog
from accounts.schema.types.types import ActivityLogType


class Logout(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    @method_decorator(login_required)
    def mutate(self, info):
        from django.contrib.auth import logout

        user = info.context.user

        # Log activity
        ActivityLog.objects.create(
            user=user,
            action="logout",
            ip_address=info.context.META.get("REMOTE_ADDR"),
            user_agent=info.context.META.get("HTTP_USER_AGENT", ""),
        )

        logout(info.context)

        return Logout(success=True, message="Logout successful")


class Mutation(graphene.ObjectType):
    logout = Logout.Field()
