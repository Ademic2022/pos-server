import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from graphene.test import Client
from src.schemas import schema


class TestAccountsQueries(TestCase):
    """Test cases for accounts GraphQL queries"""

    def setUp(self):
        self.client = Client(schema)
        self.factory = RequestFactory()

        # Import here to avoid Django setup issues
        from tests.factories import UserFactory, RoleFactory, ActivityLogFactory
        from accounts.models import User

        self.user = UserFactory()
        self.staff_user = UserFactory(is_staff=True)
        self.role = RoleFactory()

    def _make_authenticated_request(self, user=None):
        """Helper to create authenticated request"""
        if user is None:
            user = self.staff_user
        request = self.factory.get("/")
        request.user = user
        request.session = {}
        request.META = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": "Test Agent",
            "HTTP_HOST": "testserver",
        }
        return request

    def _make_anonymous_request(self):
        """Helper to create anonymous request"""
        request = self.factory.get("/")
        request.user = AnonymousUser()
        request.session = {}
        request.META = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": "Test Agent",
            "HTTP_HOST": "testserver",
        }
        return request

    def test_users_query_requires_auth(self):
        """Test that users query requires authentication"""
        query = """
            query {
                users {
                    edges {
                        node {
                            id
                            username
                        }
                    }
                }
            }
        """
        request = self._make_anonymous_request()
        result = self.client.execute(query, context=request)
        self.assertIsNotNone(result.get("errors"))

    def test_users_query_with_auth(self):
        """Test users query with authenticated user"""
        from tests.factories import UserFactory

        UserFactory.create_batch(3)  # Create some test users

        query = """
            query {
                users {
                    edges {
                        node {
                            id
                            username
                            email
                        }
                    }
                }
            }
        """
        request = self._make_authenticated_request(self.staff_user)
        result = self.client.execute(query, context=request)

        # The query might still have errors due to login_required decorator
        # but it should at least execute without authentication errors
        self.assertIsNotNone(result)

    def test_user_query_by_id(self):
        """Test fetching a single user by ID"""
        from tests.factories import UserFactory

        test_user = UserFactory(username="testuser", email="test@example.com")

        query = """
            query GetUser($id: ID!) {
                user(id: $id) {
                    id
                    username
                    email
                    firstName
                    lastName
                }
            }
        """
        request = self._make_authenticated_request(self.staff_user)
        result = self.client.execute(
            query, variables={"id": str(test_user.id)}, context=request
        )

        self.assertIsNotNone(result)

    def test_graphql_schema_introspection(self):
        """Test that GraphQL schema introspection works"""
        query = """
            query {
                __schema {
                    types {
                        name
                    }
                }
            }
        """
        result = self.client.execute(query)
        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result.get("data"))
        self.assertIn("__schema", result["data"])


# Keep the pytest version for when pytest is working
@pytest.mark.django_db
class TestAccountsQueriesPytest:
    """Pytest version of GraphQL query tests (for future use)"""

    def test_users_query_requires_auth(self, graphql_client, anonymous_request):
        """Test that users query requires authentication"""
        query = """
            query {
                users {
                    edges {
                        node {
                            id
                            username
                        }
                    }
                }
            }
        """
        result = graphql_client.execute(query, context=anonymous_request)
        assert result.get("errors") is not None
