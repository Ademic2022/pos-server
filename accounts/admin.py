from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, UserSession, ActivityLog

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
