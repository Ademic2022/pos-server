import pytest


@pytest.fixture
def test_user():
    """Fixture for a test user with specific attributes"""
    from tests.factories import UserFactory

    return UserFactory(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def admin_user():
    """Fixture for admin user"""
    from tests.factories import UserFactory

    return UserFactory(
        username="admin", email="admin@example.com", is_staff=True, is_superuser=True
    )


@pytest.fixture
def manager_role():
    """Fixture for manager role"""
    from tests.factories import RoleFactory

    return RoleFactory(name="Manager", description="Manager role")


@pytest.fixture
def manager_user(manager_role):
    """Fixture for user with manager role"""
    from tests.factories import UserFactory

    user = UserFactory(
        username="manager",
        email="manager@example.com",
        is_staff=True,
    )
    user.roles.add(manager_role)
    return user


@pytest.fixture
def user_session(test_user):
    """Fixture for user session"""
    from tests.factories import UserSessionFactory

    return UserSessionFactory(
        user=test_user, session_key="test_session_123", ip_address="192.168.1.1"
    )


@pytest.fixture
def activity_log(test_user):
    """Fixture for activity log"""
    from tests.factories import ActivityLogFactory

    return ActivityLogFactory(user=test_user, action="login", ip_address="192.168.1.1")


@pytest.fixture
def multiple_activity_logs(test_user):
    """Fixture for multiple activity logs"""
    from tests.factories import ActivityLogFactory

    return ActivityLogFactory.create_batch(5, user=test_user)
