from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin interface for Customer model"""

    list_display = (
        "name",
        "id",
        "email",
        "phone",
        "type",
        "status_badge",
        "balance",
        "credit_limit",
        "available_credit_display",
        "total_purchases",
        "last_purchase",
        "created_at",
    )

    list_filter = (
        "type",
        "status",
        "created_at",
        "last_purchase",
        "created_by",
    )

    search_fields = (
        "name",
        "email",
        "phone",
        "address",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "available_credit_display",
        "join_date",
        "total_purchases",
    )

    fieldsets = (
        ("Basic Information", {"fields": ("name", "email", "phone", "address")}),
        ("Customer Details", {"fields": ("type", "status", "notes")}),
        (
            "Financial Information",
            {
                "fields": (
                    "balance",
                    "credit_limit",
                    "available_credit_display",
                    "total_purchases",
                    "last_purchase",
                )
            },
        ),
        (
            "Audit Information",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            "active": "green",
            "inactive": "orange",
            "blocked": "red",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def available_credit_display(self, obj):
        """Display available credit with color coding"""
        from decimal import Decimal

        available = obj.available_credit()
        if available <= 0:
            color = "red"
        elif available < obj.credit_limit * Decimal("0.2"):  # Less than 20% available
            color = "orange"
        else:
            color = "green"

        return format_html(
            '<span style="color: {}; font-weight: bold;">${}</span>',
            color,
            f"{available:.2f}",
        )

    available_credit_display.short_description = "Available Credit"

    def save_model(self, request, obj, form, change):
        """Set created_by when creating new customer"""
        if not change:  # Creating new customer
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Optimize queries by selecting related data"""
        return super().get_queryset(request).select_related("created_by")

    actions = ["mark_as_active", "mark_as_inactive", "mark_as_blocked"]

    def mark_as_active(self, request, queryset):
        """Mark selected customers as active"""
        updated = queryset.update(status="active")
        self.message_user(request, f"{updated} customers marked as active.")

    mark_as_active.short_description = "Mark selected customers as active"

    def mark_as_inactive(self, request, queryset):
        """Mark selected customers as inactive"""
        updated = queryset.update(status="inactive")
        self.message_user(request, f"{updated} customers marked as inactive.")

    mark_as_inactive.short_description = "Mark selected customers as inactive"

    def mark_as_blocked(self, request, queryset):
        """Mark selected customers as blocked"""
        updated = queryset.update(status="blocked")
        self.message_user(request, f"{updated} customers marked as blocked.")

    mark_as_blocked.short_description = "Mark selected customers as blocked"
