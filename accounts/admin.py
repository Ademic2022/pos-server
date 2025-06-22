from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Role, UserSession, ActivityLog
from graphql_auth.models import UserStatus

# Register your models here.


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "email", "phone", "address")},
        ),
        ("Work info", {"fields": ("role", "employee_id", "salary")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Additional info", {"fields": ("last_login_ip", "meta")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name", "description")
    filter_horizontal = ("permissions",)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "login_time", "logout_time", "is_active")
    list_filter = ("is_active", "login_time")
    search_fields = ("user__username", "ip_address")
    readonly_fields = ("session_key", "login_time")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "model_name", "timestamp")
    list_filter = ("action", "timestamp")
    search_fields = ("user__username", "model_name", "object_repr")
    readonly_fields = ("timestamp",)


@admin.register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    """Admin interface for UserStatus model from graphql_auth"""

    list_display = (
        "user",
        "verified_badge",
        "archived_badge",
        "secondary_email",
        "user_email",
        "user_date_joined",
    )

    list_filter = (
        "verified",
        "archived",
        "user__date_joined",
        "user__is_active",
        "user__is_staff",
    )

    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "secondary_email",
    )

    readonly_fields = ("user",)

    def user_email(self, obj):
        """Display user's primary email"""
        return obj.user.email if obj.user else "N/A"

    user_email.short_description = "Primary Email"

    def user_date_joined(self, obj):
        """Display when user joined"""
        return obj.user.date_joined if obj.user else "N/A"

    user_date_joined.short_description = "Date Joined"

    def verified_badge(self, obj):
        """Display verification status with colored badge"""
        if obj.verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>', 
                "✓ Verified"
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>', 
                "✗ Not Verified"
            )

    verified_badge.short_description = "Verification Status"

    def archived_badge(self, obj):
        """Display archived status with colored badge"""
        if obj.archived:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>', 
                "📁 Archived"
            )
        else:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>', 
                "📂 Active"
            )

    archived_badge.short_description = "Archive Status"

    actions = [
        "mark_as_verified",
        "mark_as_unverified",
        "mark_as_archived",
        "mark_as_unarchived",
    ]

    def mark_as_verified(self, request, queryset):
        """Mark selected users as verified"""
        updated = queryset.update(verified=True)
        self.message_user(request, f"{updated} users marked as verified.")

    mark_as_verified.short_description = "Mark selected users as verified"

    def mark_as_unverified(self, request, queryset):
        """Mark selected users as unverified"""
        updated = queryset.update(verified=False)
        self.message_user(request, f"{updated} users marked as unverified.")

    mark_as_unverified.short_description = "Mark selected users as unverified"

    def mark_as_archived(self, request, queryset):
        """Mark selected users as archived"""
        updated = queryset.update(archived=True)
        self.message_user(request, f"{updated} users marked as archived.")

    mark_as_archived.short_description = "Mark selected users as archived"

    def mark_as_unarchived(self, request, queryset):
        """Mark selected users as unarchived"""
        updated = queryset.update(archived=False)
        self.message_user(request, f"{updated} users marked as unarchived.")

    mark_as_unarchived.short_description = "Mark selected users as unarchived"

    def get_queryset(self, request):
        """Optimize queries by selecting related user data"""
        return super().get_queryset(request).select_related("user")
