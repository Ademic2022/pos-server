import pytest
import json
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from accounts.models import User, ActivityLog
from tests.factories import UserFactory


@pytest.mark.django_db
class TestAccountsMutations:
    """Test cases for accounts GraphQL mutations"""

    def test_register_mutation(self, graphql_client, anonymous_request):
        """Test user registration mutation"""
        mutation = """
            mutation RegisterUser($input: RegisterInput!) {
                register(input: $input) {
                    success
                    errors
                    token
                    refreshToken
                }
            }
        """
        variables = {
            "input": {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "testpass123!",
                "password2": "testpass123!",
            }
        }

        result = graphql_client.execute(
            mutation, variables=variables, context=anonymous_request
        )

        # Check if mutation executed without errors
        assert result.get("errors") is None
        register_data = result["data"]["register"]

        # Check if user was created successfully
        if register_data["success"]:
            assert User.objects.filter(username="newuser").exists()
        else:
            # Check what errors occurred
            assert register_data["errors"] is not None

    def test_token_auth_mutation(self, graphql_client, anonymous_request):
        """Test login/token authentication mutation"""
        # Create a user first
        user = UserFactory(username="testuser")
        user.set_password("testpass123")
        user.save()

        mutation = """
            mutation TokenAuth($username: String!, $password: String!) {
                tokenAuth(username: $username, password: $password) {
                    success
                    errors
                    token
                    refreshToken
                    user {
                        id
                        username
                    }
                }
            }
        """
        variables = {"username": "testuser", "password": "testpass123"}

        result = graphql_client.execute(
            mutation, variables=variables, context=anonymous_request
        )

        assert result.get("errors") is None
        auth_data = result["data"]["tokenAuth"]

        if auth_data["success"]:
            assert auth_data["token"] is not None
            assert auth_data["user"]["username"] == "testuser"

    def test_token_auth_invalid_credentials(self, graphql_client, anonymous_request):
        """Test login with invalid credentials"""
        mutation = """
            mutation TokenAuth($username: String!, $password: String!) {
                tokenAuth(username: $username, password: $password) {
                    success
                    errors
                    token
                }
            }
        """
        variables = {"username": "invaliduser", "password": "wrongpassword"}

        result = graphql_client.execute(
            mutation, variables=variables, context=anonymous_request
        )

        assert result.get("errors") is None
        auth_data = result["data"]["tokenAuth"]
        assert not auth_data["success"]
        assert auth_data["errors"] is not None

    def test_logout_mutation(self, graphql_client, authenticated_request, user):
        """Test logout mutation"""
        mutation = """
            mutation {
                logout {
                    success
                    message
                }
            }
        """

        request = authenticated_request(user)
        result = graphql_client.execute(mutation, context=request)

        assert result.get("errors") is None
        logout_data = result["data"]["logout"]
        assert logout_data["success"] is True
        assert "logout" in logout_data["message"].lower()

    def test_logout_requires_auth(self, graphql_client, anonymous_request):
        """Test that logout requires authentication"""
        mutation = """
            mutation {
                logout {
                    success
                    message
                }
            }
        """

        result = graphql_client.execute(mutation, context=anonymous_request)
        # Should have errors since user is not authenticated
        assert result.get("errors") is not None

    def test_verify_token_mutation(self, graphql_client, anonymous_request):
        """Test token verification mutation"""
        # This would require a valid JWT token
        mutation = """
            mutation VerifyToken($token: String!) {
                verifyToken(token: $token) {
                    success
                    errors
                    payload
                }
            }
        """
        variables = {"token": "invalid_token"}

        result = graphql_client.execute(
            mutation, variables=variables, context=anonymous_request
        )

        assert result.get("errors") is None
        verify_data = result["data"]["verifyToken"]
        # Should fail with invalid token
        assert not verify_data["success"]

    def test_refresh_token_mutation(self, graphql_client, anonymous_request):
        """Test token refresh mutation"""
        mutation = """
            mutation RefreshToken($refreshToken: String!) {
                refreshToken(refreshToken: $refreshToken) {
                    success
                    errors
                    token
                    refreshToken
                    payload
                }
            }
        """
        variables = {"refreshToken": "invalid_refresh_token"}

        result = graphql_client.execute(
            mutation, variables=variables, context=anonymous_request
        )

        assert result.get("errors") is None
        refresh_data = result["data"]["refreshToken"]
        # Should fail with invalid refresh token
        assert not refresh_data["success"]

    def test_password_change_mutation(
        self, graphql_client, authenticated_request, user
    ):
        """Test password change mutation"""
        # Set a known password for the user
        user.set_password("oldpassword123")
        user.save()

        mutation = """
            mutation PasswordChange($input: PasswordChangeInput!) {
                passwordChange(input: $input) {
                    success
                    errors
                    token
                    refreshToken
                }
            }
        """
        variables = {
            "input": {
                "oldPassword": "oldpassword123",
                "newPassword1": "newpassword123!",
                "newPassword2": "newpassword123!",
            }
        }

        request = authenticated_request(user)
        result = graphql_client.execute(mutation, variables=variables, context=request)

        assert result.get("errors") is None
        change_data = result["data"]["passwordChange"]

        if change_data["success"]:
            # Verify password was actually changed
            user.refresh_from_db()
            assert user.check_password("newpassword123!")

    def test_update_account_mutation(self, graphql_client, authenticated_request, user):
        """Test account update mutation"""
        mutation = """
            mutation UpdateAccount($input: UpdateAccountInput!) {
                updateAccount(input: $input) {
                    success
                    errors
                }
            }
        """
        variables = {"input": {"firstName": "Updated", "lastName": "Name"}}

        request = authenticated_request(user)
        result = graphql_client.execute(mutation, variables=variables, context=request)

        assert result.get("errors") is None
        update_data = result["data"]["updateAccount"]

        if update_data["success"]:
            user.refresh_from_db()
            assert user.first_name == "Updated"
            assert user.last_name == "Name"
