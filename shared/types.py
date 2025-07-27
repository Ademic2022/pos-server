"""
Shared GraphQL types used across multiple apps
"""

import graphene


class ValueCountPair(graphene.ObjectType):
    """A pair containing a value and count - commonly used for statistics"""

    value = graphene.Decimal()
    count = graphene.Int()
