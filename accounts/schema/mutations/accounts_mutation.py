import graphene
from graphql_jwt.decorators import login_required
from accounts.models import ActivityLog
from graphql_auth.utils import revoke_user_refresh_token

# from accounts.schema.types.types import ActivityLogType


class Logout(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info):
        user = info.context.user

        # Log activity
        ActivityLog.objects.create(
            user=user,
            action="logout",
            ip_address=getattr(info.context, "META", {}).get("REMOTE_ADDR"),
            user_agent=getattr(info.context, "META", {}).get("HTTP_USER_AGENT", ""),
        )

        # Clear session if it exists
        if hasattr(info.context, "session") and hasattr(info.context.session, "flush"):
            info.context.session.flush()

        revoke_user_refresh_token(user=user)

        return Logout(success=True, message="Logout successful")


class Mutation(graphene.ObjectType):
    logout = Logout.Field()
