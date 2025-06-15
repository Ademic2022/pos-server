from django.db import models
from django.contrib.auth.models import User, Permission
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    PermissionsMixin,
    AbstractBaseUser,
)
from accounts.choices import AccountStatusChoices, ActionChoices


NULL = {"null": True, "blank": True}


class UserManager(BaseUserManager):
    def create(self, username, **kwargs):
        if username is None:
            raise ValueError("username can not be null")

        user = self.model(username=username, **kwargs)
        user.set_password(kwargs.get("password"))
        user.save(using=self._db)
        return user

    def create_superuser(self, username, **kwargs):
        kwargs["is_staff"] = True
        kwargs["is_superuser"] = True
        return self.create(username=username, **kwargs)

    def create_user(self, username, **kwargs):
        return self.create(username=username, **kwargs)


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(**NULL)
    permissions = models.ManyToManyField(Permission, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, **NULL)
    phone = models.CharField(max_length=20, **NULL)
    address = models.TextField(**NULL)
    employee_id = models.CharField(max_length=20, unique=True, **NULL)
    salary = models.DecimalField(max_digits=10, decimal_places=2, **NULL)
    status = models.CharField(
        max_length=10,
        choices=AccountStatusChoices.choices,
        default=AccountStatusChoices.ACTIVE,
    )
    last_login_ip = models.GenericIPAddressField(**NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta = models.JSONField(default=dict, **NULL)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.username})"

    def has_permission(self, permission_codename):
        """Check if user has specific permission through role or direct assignment"""
        # Check direct user permissions
        if self.user.has_perm(permission_codename):
            return True

        # Check role permissions
        if self.role:
            return self.role.permissions.filter(codename=permission_codename).exists()

        return False


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_key = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(**NULL)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(**NULL)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "user_sessions"
        ordering = ["-login_time"]

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, **NULL)
    action = models.CharField(max_length=20, choices=ActionChoices.choices)
    model_name = models.CharField(max_length=50, **NULL)
    object_id = models.PositiveIntegerField(**NULL)
    object_repr = models.CharField(max_length=200, **NULL)
    changes = models.JSONField(**NULL)
    ip_address = models.GenericIPAddressField(**NULL)
    user_agent = models.TextField(**NULL)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activity_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
