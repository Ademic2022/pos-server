import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from graphql_auth.models import UserStatus
from accounts.admin import UserStatusAdmin
from tests.factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserStatusAdmin:
    """Test cases for UserStatus admin interface"""

    def test_user_status_admin_registered(self):
        """Test that UserStatusAdmin is properly registered"""
        assert admin.site.is_registered(UserStatus)
        assert isinstance(admin.site._registry[UserStatus], UserStatusAdmin)

    def test_verified_badge_method(self):
        """Test verified badge display method"""
        admin_instance = UserStatusAdmin(UserStatus, admin.site)
        user = UserFactory()

        # Get the automatically created UserStatus
        user_status = UserStatus.objects.get(user=user)
        
        # Test verified status
        user_status.verified = True
        user_status.save()
        badge_html = admin_instance.verified_badge(user_status)
        assert "green" in badge_html
        assert "✓ Verified" in badge_html

        # Test unverified status
        user_status.verified = False
        user_status.save()
        badge_html = admin_instance.verified_badge(user_status)
        assert "red" in badge_html
        assert "✗ Not Verified" in badge_html

    def test_archived_badge_method(self):
        """Test archived badge display method"""
        admin_instance = UserStatusAdmin(UserStatus, admin.site)
        user = UserFactory()

        # Get the automatically created UserStatus
        user_status = UserStatus.objects.get(user=user)
        
        # Test archived status
        user_status.archived = True
        user_status.save()
        badge_html = admin_instance.archived_badge(user_status)
        assert "red" in badge_html
        assert "📁 Archived" in badge_html

        # Test active (not archived) status
        user_status.archived = False
        user_status.save()
        badge_html = admin_instance.archived_badge(user_status)
        assert "green" in badge_html
        assert "📂 Active" in badge_html

    def test_user_email_method(self):
        """Test user email display method"""
        admin_instance = UserStatusAdmin(UserStatus, admin.site)
        user = UserFactory(email="test@example.com")
        user_status = UserStatus.objects.get(user=user)

        email = admin_instance.user_email(user_status)
        assert email == "test@example.com"

        # Test edge case: user with no email
        user.email = ""
        user.save()
        user_status.refresh_from_db()  # Refresh to get updated user data
        email = admin_instance.user_email(user_status)
        assert email == ""

    def test_user_date_joined_method(self):
        """Test user date joined display method"""
        admin_instance = UserStatusAdmin(UserStatus, admin.site)
        user = UserFactory()
        user_status = UserStatus.objects.get(user=user)

        date_joined = admin_instance.user_date_joined(user_status)
        assert date_joined == user.date_joined

    def test_admin_actions_verify_users(self, rf):
        """Test admin actions for verification management"""
        from django.contrib.messages.storage.fallback import FallbackStorage

        user = UserFactory()
        request = rf.get("/")
        request.user = user

        # Add message storage to request
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))

        admin_instance = UserStatusAdmin(UserStatus, admin.site)

        # Create unverified user statuses - get existing ones
        users = [UserFactory() for _ in range(3)]
        user_statuses = [
            UserStatus.objects.get(user=u) for u in users
        ]
        
        # Make sure they're unverified initially
        for user_status in user_statuses:
            user_status.verified = False
            user_status.save()
        
        queryset = UserStatus.objects.filter(
            id__in=[us.id for us in user_statuses]
        )

        # Test mark as verified action
        admin_instance.mark_as_verified(request, queryset)

        # Refresh from database
        for user_status in user_statuses:
            user_status.refresh_from_db()
            assert user_status.verified is True

        # Test mark as unverified action
        admin_instance.mark_as_unverified(request, queryset)

        # Refresh from database
        for user_status in user_statuses:
            user_status.refresh_from_db()
            assert user_status.verified is False

    def test_admin_actions_archive_users(self, rf):
        """Test admin actions for archival management"""
        from django.contrib.messages.storage.fallback import FallbackStorage

        user = UserFactory()
        request = rf.get("/")
        request.user = user

        # Add message storage to request
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))

        admin_instance = UserStatusAdmin(UserStatus, admin.site)

        # Create active user statuses - get existing ones
        users = [UserFactory() for _ in range(3)]
        user_statuses = [
            UserStatus.objects.get(user=u) for u in users
        ]
        
        # Make sure they're not archived initially
        for user_status in user_statuses:
            user_status.archived = False
            user_status.save()
        
        queryset = UserStatus.objects.filter(
            id__in=[us.id for us in user_statuses]
        )

        # Test mark as archived action
        admin_instance.mark_as_archived(request, queryset)

        # Refresh from database
        for user_status in user_statuses:
            user_status.refresh_from_db()
            assert user_status.archived is True

        # Test mark as unarchived action
        admin_instance.mark_as_unarchived(request, queryset)

        # Refresh from database
        for user_status in user_statuses:
            user_status.refresh_from_db()
            assert user_status.archived is False

    def test_list_display_fields(self):
        """Test that all list_display fields are accessible"""
        admin_instance = UserStatusAdmin(UserStatus, admin.site)
        user = UserFactory()
        user_status = UserStatus.objects.get(user=user)

        # Test that all list_display methods work
        assert admin_instance.verified_badge(user_status) is not None
        assert admin_instance.archived_badge(user_status) is not None
        assert admin_instance.user_email(user_status) is not None
        assert admin_instance.user_date_joined(user_status) is not None

    def test_search_functionality(self):
        """Test that search fields are properly configured"""
        admin_instance = UserStatusAdmin(UserStatus, admin.site)

        # Verify search fields are set
        expected_search_fields = (
            "user__username",
            "user__email",
            "user__first_name",
            "user__last_name",
            "secondary_email",
        )
        assert admin_instance.search_fields == expected_search_fields

    def test_list_filters(self):
        """Test that list filters are properly configured"""
        admin_instance = UserStatusAdmin(UserStatus, admin.site)

        expected_filters = (
            "verified",
            "archived",
            "user__date_joined",
            "user__is_active",
            "user__is_staff",
        )
        assert admin_instance.list_filter == expected_filters

    def test_queryset_optimization(self):
        """Test that get_queryset properly optimizes queries"""
        admin_instance = UserStatusAdmin(UserStatus, admin.site)
        
        # Create a mock request
        class MockRequest:
            pass
        
        request = MockRequest()
        queryset = admin_instance.get_queryset(request)
        
        # Check that select_related is applied
        assert "user" in queryset.query.select_related

    def test_readonly_fields(self):
        """Test that readonly fields are properly configured"""
        admin_instance = UserStatusAdmin(UserStatus, admin.site)
        
        expected_readonly_fields = ("user",)
        assert admin_instance.readonly_fields == expected_readonly_fields

    def test_actions_list(self):
        """Test that all expected actions are configured"""
        admin_instance = UserStatusAdmin(UserStatus, admin.site)
        
        expected_actions = [
            "mark_as_verified",
            "mark_as_unverified", 
            "mark_as_archived",
            "mark_as_unarchived",
        ]
        assert admin_instance.actions == expected_actions
