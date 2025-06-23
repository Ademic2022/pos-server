from django.contrib import admin
from django.utils.html import format_html
from decimal import Decimal
from products.models import Product
from products.choices import SaleType


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin interface for Product model"""

    # List display configuration
    list_display = [
        "name",
        "formatted_price",
        "unit",
        "sale_type_badge",
        "stock_status",
        "created_at",
        "updated_at",
    ]

    # List filters
    list_filter = [
        "sale_type",
        "created_at",
        "updated_at",
    ]

    # Search functionality
    search_fields = [
        "name",
    ]

    # Ordering
    ordering = ["sale_type", "name"]

    # Read-only fields
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "stock_status",
    ]

    # Fieldsets for organized form layout
    fieldsets = (
        ("Product Information", {"fields": ("name", "price", "unit")}),
        ("Classification", {"fields": ("sale_type",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    # Actions
    actions = ["mark_as_retail", "mark_as_wholesale", "reset_units"]

    def formatted_price(self, obj):
        """Display price with currency formatting"""
        return f"${obj.price:.2f}"

    formatted_price.short_description = "Price"
    formatted_price.admin_order_field = "price"

    def sale_type_badge(self, obj):
        """Display sale type with color-coded badge"""
        if obj.sale_type == SaleType.WHOLESALE:
            color = "blue"
            icon = "🏢"
        else:  # RETAIL
            color = "green"
            icon = "🛒"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_sale_type_display(),
        )

    sale_type_badge.short_description = "Sale Type"
    sale_type_badge.admin_order_field = "sale_type"

    def stock_status(self, obj):
        """Display stock status with color coding"""
        if obj.unit == 0:
            color = "red"
            status = "Out of Stock"
        elif obj.unit < 10:
            color = "orange"
            status = "Low Stock"
        else:
            color = "green"
            status = "In Stock"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({})</span>',
            color,
            status,
            obj.unit,
        )

    stock_status.short_description = "Stock Status"

    # Admin actions
    def mark_as_retail(self, request, queryset):
        """Mark selected products as retail"""
        updated = queryset.update(sale_type=SaleType.RETAIL)
        self.message_user(
            request, f"{updated} product(s) successfully marked as retail."
        )

    mark_as_retail.short_description = "Mark selected products as retail"

    def mark_as_wholesale(self, request, queryset):
        """Mark selected products as wholesale"""
        updated = queryset.update(sale_type=SaleType.WHOLESALE)
        self.message_user(
            request, f"{updated} product(s) successfully marked as wholesale."
        )

    mark_as_wholesale.short_description = "Mark selected products as wholesale"

    def reset_units(self, request, queryset):
        """Reset units to 0 for selected products"""
        updated = queryset.update(unit=0)
        self.message_user(request, f"Units reset to 0 for {updated} product(s).")

    reset_units.short_description = "Reset units to 0"
