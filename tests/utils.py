"""
Test utilities for GraphQL testing
"""

import json
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from graphene.test import Client


def execute_graphql_query(schema, query, variables=None, context=None, user=None):
    """
    Helper function to execute GraphQL queries with proper context
    """
    client = Client(schema)

    if context is None and user is not None:
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user if user else AnonymousUser()
        request.session = {}
        request.META = {"REMOTE_ADDR": "127.0.0.1", "HTTP_USER_AGENT": "Test Agent"}
        context = request

    return client.execute(query, variables=variables, context=context)


def assert_graphql_success(result):
    """
    Assert that a GraphQL result was successful (no errors)
    """
    assert result.get("errors") is None, f"GraphQL errors: {result.get('errors')}"
    assert result.get("data") is not None


def assert_graphql_error(result, error_message=None):
    """
    Assert that a GraphQL result has errors
    """
    assert result.get("errors") is not None
    if error_message:
        error_messages = [str(error) for error in result.get("errors", [])]
        assert any(
            error_message in msg for msg in error_messages
        ), f"Expected error '{error_message}' not found in {error_messages}"


def get_graphql_field_data(result, field_path):
    """
    Get data from a GraphQL result using a dot-separated field path
    Example: get_graphql_field_data(result, 'data.users.edges.0.node.username')
    """
    data = result
    for field in field_path.split("."):
        if field.isdigit():
            data = data[int(field)]
        else:
            data = data[field]
    return data


class GraphQLTestMixin:
    """
    Mixin class for GraphQL testing that provides common methods
    """

    def execute_query(self, query, variables=None, user=None):
        """Execute a GraphQL query with optional user authentication"""
        from src.schemas import schema

        return execute_graphql_query(schema, query, variables, user=user)

    def assert_query_success(self, result):
        """Assert query was successful"""
        assert_graphql_success(result)

    def assert_query_error(self, result, error_message=None):
        """Assert query had errors"""
        assert_graphql_error(result, error_message)
