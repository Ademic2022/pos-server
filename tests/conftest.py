import pytest
import os
import django
from django.conf import settings

# Configure Django settings for tests
if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
    django.setup()


@pytest.fixture
def graphql_client():
    """Fixture for GraphQL client"""
    from graphene.test import Client
    from src.schemas import schema

    return Client(schema)


@pytest.fixture
def request_factory():
    """Fixture for Django request factory"""
    from django.test import RequestFactory

    return RequestFactory()


@pytest.fixture
def anonymous_user():
    """Fixture for anonymous user"""
    from django.contrib.auth.models import AnonymousUser

    return AnonymousUser()


@pytest.fixture
def user(db):
    """Fixture for regular user"""
    from tests.factories import UserFactory

    return UserFactory()


@pytest.fixture
def staff_user(db):
    """Fixture for staff user"""
    from tests.factories import UserFactory

    return UserFactory(is_staff=True)


@pytest.fixture
def superuser(db):
    """Fixture for superuser"""
    from tests.factories import SuperUserFactory

    return SuperUserFactory()


@pytest.fixture
def role(db):
    """Fixture for role"""
    from tests.factories import RoleFactory

    return RoleFactory()


@pytest.fixture
def admin_role(db):
    """Fixture for admin role"""
    from tests.factories import RoleFactory

    return RoleFactory(name="Admin", description="Administrator role")


@pytest.fixture
def manager_role(db):
    """Fixture for manager role"""
    from tests.factories import RoleFactory

    return RoleFactory(name="Manager", description="Manager role")


@pytest.fixture
def authenticated_request(request_factory):
    """Fixture for authenticated request"""

    def _make_request(user_obj=None, path="/", method="GET"):
        if user_obj is None:
            from tests.factories import UserFactory

            user_obj = UserFactory()

        if method.upper() == "POST":
            request = request_factory.post(path)
        else:
            request = request_factory.get(path)

        request.user = user_obj
        request.session = {}
        request.META = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": "Test Agent",
            "HTTP_HOST": "testserver",
        }
        return request

    return _make_request


@pytest.fixture
def anonymous_request(request_factory, anonymous_user):
    """Fixture for anonymous request"""
    request = request_factory.get("/")
    request.user = anonymous_user
    request.session = {}
    request.META = {
        "REMOTE_ADDR": "127.0.0.1",
        "HTTP_USER_AGENT": "Test Agent",
        "HTTP_HOST": "testserver",
    }
    return request


@pytest.fixture
def multiple_users(db):
    """Fixture for creating multiple test users"""
    from tests.factories import UserFactory

    return UserFactory.create_batch(5)


@pytest.fixture
def user_with_role(role):
    """Fixture for user with a role"""
    from tests.factories import UserFactory

    return UserFactory(role=role)


@pytest.fixture
def user_with_token(db, client):
    """Create a user and authenticate them for GraphQL requests"""
    from tests.factories import UserFactory

    user = UserFactory()
    client.force_login(user)
    return user


@pytest.fixture
def authenticated_user(db):
    """Create an authenticated user for GraphQL context"""
    from tests.factories import UserFactory

    return UserFactory()


@pytest.fixture
def customer(db):
    """Fixture for a single customer"""
    from tests.factories import CustomerFactory

    return CustomerFactory()


@pytest.fixture
def customers(db):
    """Fixture for multiple customers"""
    from tests.factories import CustomerFactory

    return CustomerFactory.create_batch(5)


@pytest.fixture
def graphql_request_factory():
    """Factory for creating GraphQL request objects"""
    from django.test import RequestFactory

    def _create_request(user=None, path="/graphql/"):
        factory = RequestFactory()
        request = factory.post(path)
        request.user = user
        request.session = {}
        request.META = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": "Test Agent",
            "HTTP_HOST": "testserver",
        }
        return request

    return _create_request
