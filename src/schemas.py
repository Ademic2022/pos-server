import graphene
from accounts.schema.queries import accounts_query
from accounts.schema.mutations import accounts_mutation
from customers.schema.queries import customer_queries
from customers.schema.mutations import customer_mutations
from graphql_auth import mutations


class AuthMutation(graphene.ObjectType):
    register = mutations.Register.Field()
    verify_account = mutations.VerifyAccount.Field()
    resend_activation_email = mutations.ResendActivationEmail.Field()
    send_password_reset_email = mutations.SendPasswordResetEmail.Field()
    password_reset = mutations.PasswordReset.Field()
    password_change = mutations.PasswordChange.Field()
    update_account = mutations.UpdateAccount.Field()
    archive_account = mutations.ArchiveAccount.Field()
    delete_account = mutations.DeleteAccount.Field()

    # django-graphql-jwt inheritances
    token_auth = mutations.ObtainJSONWebToken.Field()
    verify_token = mutations.VerifyToken.Field()
    refresh_token = mutations.RefreshToken.Field()
    revoke_token = mutations.RevokeToken.Field()


class Query(accounts_query.Query, customer_queries.Query):
    pass


class Mutation(
    AuthMutation,
    accounts_mutation.Mutation,
    customer_mutations.Mutation,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
