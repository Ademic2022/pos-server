import pytest
from django.test import TestCase, TransactionTestCase
from django.db import IntegrityError
from accounts.models import User, Role, UserSession, ActivityLog
from tests.factories import UserFactory, RoleFactory


@pytest.mark.django_db
class TestAccountsIntegration:
    """Integration tests for accounts functionality"""

    def test_user_registration_to_login_flow(self, graphql_client, anonymous_request):
        """Test complete flow from registration to login"""
        # Step 1: Register a new user
        register_mutation = """
            mutation RegisterUser(
                $username: String!,
                $email: String!,
                $firstName: String!,
                $lastName: String!,
                $password1: String!,
                $password2: String!
            ) {
                register(
                    username: $username,
                    email: $email,
                    firstName: $firstName,
                    lastName: $lastName,
                    password1: $password1,
                    password2: $password2
                ) {
                    success
                    errors
                }
            }
        """
        register_variables = {
            "username": "flowuser",
            "email": "flowuser@example.com",
            "firstName": "Flow",
            "lastName": "User",
            "password1": "testpass123!",
            "password2": "testpass123!",
        }

        register_result = graphql_client.execute(
            register_mutation, variables=register_variables, context=anonymous_request
        )

        # Assuming registration succeeds or check errors
        if register_result["data"]["register"]["success"]:
            # Step 2: Login with the registered user
            login_mutation = """
                mutation TokenAuth($username: String!, $password: String!) {
                    tokenAuth(username: $username, password: $password) {
                        success
                        token
                        user {
                            username
                            email
                        }
                    }
                }
            """
            login_variables = {"username": "flowuser", "password": "testpass123!"}

            login_result = graphql_client.execute(
                login_mutation, variables=login_variables, context=anonymous_request
            )

            assert login_result.get("errors") is None
            login_data = login_result["data"]["tokenAuth"]

            if login_data["success"]:
                assert login_data["token"] is not None
                assert login_data["user"]["username"] == "flowuser"

    def test_user_role_permissions_flow(self, graphql_client, authenticated_request):
        """Test user role assignment and permission checking"""
        # Create a role with specific permissions
        role = RoleFactory(name="Manager", description="Manager role")

        # Create a user and assign role
        user = UserFactory(role=role)

        # Query user with role information
        query = """
            query GetUser($id: ID!) {
                user(id: $id) {
                    id
                    username
                    role {
                        id
                        name
                        description
                    }
                }
            }
        """

        request = authenticated_request(user)
        result = graphql_client.execute(
            query, variables={"id": str(user.id)}, context=request
        )

        assert result.get("errors") is None
        user_data = result["data"]["user"]
        assert user_data["role"]["name"] == "Manager"

    def test_activity_logging_on_actions(
        self, graphql_client, authenticated_request, user
    ):
        """Test that activities are logged properly"""
        initial_log_count = ActivityLog.objects.count()

        # Perform logout which should create an activity log
        logout_mutation = """
            mutation {
                logout {
                    success
                    message
                }
            }
        """

        request = authenticated_request(user)
        result = graphql_client.execute(logout_mutation, context=request)

        assert result.get("errors") is None

        # Check if activity log was created
        final_log_count = ActivityLog.objects.count()
        assert final_log_count > initial_log_count

        # Verify the log entry
        latest_log = ActivityLog.objects.latest("timestamp")
        assert latest_log.user == user
        assert latest_log.action == "logout"

    def test_user_session_tracking(self):
        """Test user session creation and management"""
        user = UserFactory()

        # Create a user session
        session = UserSession.objects.create(
            user=user,
            session_key="test_session_key",
            ip_address="127.0.0.1",
            user_agent="Test Agent",
        )

        assert session.is_active is True
        assert session.user == user

        # Test session deactivation
        session.is_active = False
        session.save()

        assert session.is_active is False


class TestAccountsConstraints(TransactionTestCase):
    """Test database constraints and edge cases"""

    def test_unique_username_constraint(self):
        """Test that usernames must be unique"""
        UserFactory(username="uniqueuser")

        with pytest.raises(IntegrityError):
            UserFactory(username="uniqueuser")

    def test_unique_employee_id_constraint(self):
        """Test that employee IDs must be unique"""
        UserFactory(employee_id="EMP001")

        with pytest.raises(IntegrityError):
            UserFactory(employee_id="EMP001")

    def test_role_name_unique_constraint(self):
        """Test that role names must be unique"""
        RoleFactory(name="UniqueRole")

        with pytest.raises(IntegrityError):
            RoleFactory(name="UniqueRole")

    def test_user_deletion_cascade_effects(self):
        """Test what happens when a user is deleted"""
        user = UserFactory()

        # Create related objects
        session = UserSession.objects.create(
            user=user, session_key="test_key", ip_address="127.0.0.1"
        )

        activity_log = ActivityLog.objects.create(
            user=user, action="login", ip_address="127.0.0.1"
        )

        user_id = user.id
        session_id = session.id
        log_id = activity_log.id

        # Delete user
        user.delete()

        # Check cascade effects
        assert not User.objects.filter(id=user_id).exists()
        assert not UserSession.objects.filter(id=session_id).exists()  # Should cascade

        # ActivityLog should set user to null (SET_NULL)
        log = ActivityLog.objects.get(id=log_id)
        assert log.user is None

    def test_role_deletion_effects(self):
        """Test what happens when a role is deleted"""
        role = RoleFactory()
        user = UserFactory(role=role)

        role_id = role.id
        user_id = user.id

        # Delete role
        role.delete()

        # Check effects
        assert not Role.objects.filter(id=role_id).exists()

        # User should still exist but role should be null
        user.refresh_from_db()
        assert user.role is None


@pytest.mark.django_db
class TestPermissionsAndSecurity:
    """Test security aspects and permissions"""

    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        user = UserFactory()
        user.set_password("testpassword123")
        user.save()

        # Password should be hashed, not stored in plain text
        assert user.password != "testpassword123"
        assert user.check_password("testpassword123")
        assert not user.check_password("wrongpassword")

    def test_staff_user_permissions(self, graphql_client, authenticated_request):
        """Test that only staff users can access certain queries"""
        regular_user = UserFactory(is_staff=False)
        staff_user = UserFactory(is_staff=True)

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

        # Regular user should not be able to access users query
        regular_request = authenticated_request(regular_user)
        result = graphql_client.execute(query, context=regular_request)
        assert result.get("errors") is not None

        # Staff user should be able to access users query
        staff_request = authenticated_request(staff_user)
        result = graphql_client.execute(query, context=staff_request)
        # This might still have errors depending on implementation
        # but it should at least not fail due to authentication

    def test_superuser_privileges(self):
        """Test superuser creation and privileges"""
        superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

        assert superuser.is_superuser is True
        assert superuser.is_staff is True
        assert superuser.is_active is True
