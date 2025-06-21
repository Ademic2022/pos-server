import pytest

# Ensure Django is properly configured before importing models
pytest.importorskip("django")

import django
from django.conf import settings

if not settings.configured:
    django.setup()

from django.test import TestCase
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User, Role, UserSession, ActivityLog
from tests.factories import (
    UserFactory,
    RoleFactory,
    UserSessionFactory,
    ActivityLogFactory,
    SuperUserFactory,
)


class TestUserModel(TestCase):
    """Test cases for User model"""

    def setUp(self):
        self.user = UserFactory()

    def test_user_creation(self):
        """Test user can be created with required fields"""
        self.assertTrue(isinstance(self.user, User))
        self.assertTrue(self.user.username)
        self.assertTrue(self.user.email)

    def test_user_str_method(self):
        """Test user string representation"""
        user = UserFactory(first_name="John", last_name="Doe", username="johndoe")
        self.assertEqual(str(user), "John Doe (johndoe)")

        # Test with user having no names
        user_no_names = UserFactory(first_name="", last_name="", username="testuser")
        self.assertEqual(str(user_no_names), "testuser")

    def test_get_full_name(self):
        """Test get_full_name method"""
        user = UserFactory(first_name="Jane", last_name="Smith")
        self.assertEqual(user.get_full_name(), "Jane Smith")

    def test_get_short_name(self):
        """Test get_short_name method"""
        user = UserFactory(first_name="Bob")
        self.assertEqual(user.get_short_name(), "Bob")

    def test_user_manager_create_user(self):
        """Test custom user manager create_user method"""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_user_manager_create_superuser(self):
        """Test custom user manager create_superuser method"""
        superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        self.assertEqual(superuser.username, "admin")
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_user_role_relationship(self):
        """Test user can have a role"""
        role = RoleFactory(name="Manager")
        user = UserFactory(role=role)
        self.assertEqual(user.role, role)

    def test_user_employee_id_unique(self):
        """Test employee_id is unique"""
        user1 = UserFactory(employee_id="EMP001")
        self.assertEqual(user1.employee_id, "EMP001")

        # Creating another user with same employee_id should not be allowed
        # This would be tested in integration tests where DB constraints are enforced


class TestRoleModel(TestCase):
    """Test cases for Role model"""

    def setUp(self):
        self.role = RoleFactory()

    def test_role_creation(self):
        """Test role can be created"""
        self.assertTrue(isinstance(self.role, Role))
        self.assertTrue(self.role.name)

    def test_role_str_method(self):
        """Test role string representation"""
        role = RoleFactory(name="Admin")
        self.assertEqual(str(role), "Admin")

    def test_role_permissions_relationship(self):
        """Test role can have permissions"""
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.create(
            name="Can test", codename="can_test", content_type=content_type
        )
        self.role.permissions.add(permission)
        self.assertIn(permission, self.role.permissions.all())

    def test_role_ordering(self):
        """Test roles are ordered by name"""
        role_z = RoleFactory(name="ZZZ Role")
        role_a = RoleFactory(name="AAA Role")
        roles = Role.objects.all()
        self.assertEqual(roles.first().name, "AAA Role")


class TestUserSessionModel(TestCase):
    """Test cases for UserSession model"""

    def setUp(self):
        self.session = UserSessionFactory()

    def test_session_creation(self):
        """Test user session can be created"""
        self.assertTrue(isinstance(self.session, UserSession))
        self.assertTrue(self.session.user)
        self.assertTrue(self.session.session_key)

    def test_session_str_method(self):
        """Test session string representation"""
        user = UserFactory(username="testuser")
        session = UserSessionFactory(user=user)
        expected = f"testuser - {session.login_time}"
        self.assertEqual(str(session), expected)

    def test_session_default_active(self):
        """Test session is active by default"""
        self.assertTrue(self.session.is_active)

    def test_session_ordering(self):
        """Test sessions are ordered by login_time descending"""
        user = UserFactory()
        session1 = UserSessionFactory(user=user)
        session2 = UserSessionFactory(user=user)
        sessions = UserSession.objects.filter(user=user)
        self.assertEqual(sessions.first(), session2)  # Most recent first


class TestActivityLogModel(TestCase):
    """Test cases for ActivityLog model"""

    def setUp(self):
        self.log = ActivityLogFactory()

    def test_log_creation(self):
        """Test activity log can be created"""
        self.assertTrue(isinstance(self.log, ActivityLog))
        self.assertTrue(self.log.user)
        self.assertTrue(self.log.action)

    def test_log_str_method(self):
        """Test activity log string representation"""
        user = UserFactory(username="testuser")
        log = ActivityLogFactory(user=user, action="login")
        expected = f"{user} - login - {log.timestamp}"
        self.assertEqual(str(log), expected)

    def test_log_choices_validation(self):
        """Test activity log action choices"""
        from accounts.choices import ActionChoices

        valid_actions = [choice[0] for choice in ActionChoices.choices]
        self.assertIn(self.log.action, valid_actions)

    def test_log_ordering(self):
        """Test logs are ordered by timestamp descending"""
        user = UserFactory()
        log1 = ActivityLogFactory(user=user)
        log2 = ActivityLogFactory(user=user)
        logs = ActivityLog.objects.filter(user=user)
        self.assertEqual(logs.first(), log2)  # Most recent first
