"""
Test the test setup and infrastructure
"""

import pytest
from django.test import TestCase


class TestTestInfrastructure(TestCase):
    """Test that our test infrastructure is working correctly"""

    def test_user_factory(self):
        """Test that UserFactory creates valid users"""
        from accounts.models import User
        from tests.factories import UserFactory

        user = UserFactory()
        self.assertIsInstance(user, User)
        self.assertTrue(user.username)
        self.assertTrue(user.email)
        self.assertTrue(user.is_active)

    def test_role_factory(self):
        """Test that RoleFactory creates valid roles"""
        from accounts.models import Role
        from tests.factories import RoleFactory

        role = RoleFactory()
        self.assertIsInstance(role, Role)
        self.assertTrue(role.name)

    def test_user_factory_with_role(self):
        """Test creating user with role"""
        from tests.factories import RoleFactory, UserFactory

        role = RoleFactory(name="Test Role")
        user = UserFactory(role=role)
        self.assertEqual(user.role, role)
        self.assertEqual(user.role.name, "Test Role")


@pytest.mark.django_db
class TestPytestInfrastructure:
    """Test pytest-specific infrastructure"""

    def test_database_access(self):
        """Test that pytest can access the database"""
        from accounts.models import User
        from tests.factories import UserFactory

        user = UserFactory()
        assert User.objects.filter(id=user.id).exists()

    def test_graphql_client_fixture(self, graphql_client):
        """Test that GraphQL client fixture works"""
        query = """
            query {
                __schema {
                    types {
                        name
                    }
                }
            }
        """
        result = graphql_client.execute(query)
        assert result.get("errors") is None
        assert result.get("data") is not None

    def test_authenticated_request_fixture(self, authenticated_request, user):
        """Test authenticated request fixture"""
        request = authenticated_request(user)
        assert request.user == user
        assert hasattr(request, "session")
        assert hasattr(request, "META")

    def test_anonymous_request_fixture(self, anonymous_request):
        """Test anonymous request fixture"""
        assert not anonymous_request.user.is_authenticated
        assert hasattr(anonymous_request, "session")

    def test_multiple_users_fixture(self, multiple_users):
        """Test multiple users fixture"""
        from accounts.models import User

        assert len(multiple_users) == 5
        assert all(isinstance(user, User) for user in multiple_users)

    def test_user_with_role_fixture(self, user_with_role):
        """Test user with role fixture"""
        from accounts.models import Role

        assert user_with_role.role is not None
        assert isinstance(user_with_role.role, Role)
