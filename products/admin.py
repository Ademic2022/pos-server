from django.contrib import admin
from django.utils.html import format_html
from decimal import Decimal
from products.models import Product, StockData
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


@admin.register(StockData)
class StockDataAdmin(admin.ModelAdmin):
    """Admin interface for StockData model"""

    # List display configuration
    list_display = [
        "id",
        "supplier",
        "delivered_quantity_display",
        "formatted_price",
        "cumulative_stock_display",
        "remaining_stock_display",
        "sold_stock_display",
        "stock_utilization_badge",
        "created_at",
    ]

    # List filters
    list_filter = [
        "supplier",
        "created_at",
        "updated_at",
    ]

    # Search functionality
    search_fields = [
        "supplier",
    ]

    # Ordering
    ordering = ["-created_at"]

    # Read-only fields
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "stock_utilization_percentage",
        "previous_remaining_stock",
    ]

    # Fieldsets for organized form layout
    fieldsets = (
        (
            "Delivery Information",
            {"fields": ("delivered_quantity", "price", "supplier")},
        ),
        (
            "Stock Levels",
            {"fields": ("cumulative_stock", "remaining_stock", "sold_stock")},
        ),
        (
            "Calculations",
            {
                "fields": ("stock_utilization_percentage", "previous_remaining_stock"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # Actions
    actions = ["reset_sold_stock", "update_remaining_stock"]

    def delivered_quantity_display(self, obj):
        """Display delivered quantity with litres unit"""
        try:
            quantity = float(obj.delivered_quantity)
            return f"{quantity:,.0f}L"
        except (ValueError, TypeError):
            return f"{obj.delivered_quantity}L"

    delivered_quantity_display.short_description = "Delivered"
    delivered_quantity_display.admin_order_field = "delivered_quantity"

    def formatted_price(self, obj):
        """Display price with currency formatting"""
        try:
            price = float(obj.price)
            return f"${price:.2f}/L"
        except (ValueError, TypeError):
            return f"${obj.price}/L"

    formatted_price.short_description = "Price/Unit"
    formatted_price.admin_order_field = "price"

    def cumulative_stock_display(self, obj):
        """Display cumulative stock with formatting"""
        try:
            stock = float(obj.cumulative_stock)
            return f"{stock:,.0f}L"
        except (ValueError, TypeError):
            return f"{obj.cumulative_stock}L"

    cumulative_stock_display.short_description = "Cumulative Stock"
    cumulative_stock_display.admin_order_field = "cumulative_stock"

    def remaining_stock_display(self, obj):
        """Display remaining stock with color coding"""
        try:
            remaining_stock = float(obj.remaining_stock)
            cumulative_stock = float(obj.cumulative_stock)

            percentage = (
                (remaining_stock / cumulative_stock * 100)
                if cumulative_stock > 0
                else 0
            )

            if percentage < 20:
                color = "red"
            elif percentage < 50:
                color = "orange"
            else:
                color = "green"

            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.0f}L</span>',
                color,
                remaining_stock,
            )
        except (ValueError, TypeError, ZeroDivisionError):
            # Fallback for any formatting issues
            return f"{obj.remaining_stock}L"

    remaining_stock_display.short_description = "Remaining"
    remaining_stock_display.admin_order_field = "remaining_stock"

    def sold_stock_display(self, obj):
        """Display sold stock with formatting"""
        try:
            stock = float(obj.sold_stock)
            return f"{stock:,.0f}L"
        except (ValueError, TypeError):
            return f"{obj.sold_stock}L"

    sold_stock_display.short_description = "Sold"
    sold_stock_display.admin_order_field = "sold_stock"

    def stock_utilization_badge(self, obj):
        """Display stock utilization percentage with color-coded badge"""
        try:
            # Ensure we get a numeric value
            percentage = float(obj.stock_utilization_percentage)
        except (ValueError, TypeError):
            # Fallback calculation if property returns non-numeric value
            if obj.cumulative_stock > 0:
                percentage = (obj.sold_stock / obj.cumulative_stock) * 100
            else:
                percentage = 0.0

        if percentage < 30:
            color = "orange"
            status = "Low Sales"
        elif percentage < 70:
            color = "blue"
            status = "Moderate"
        else:
            color = "green"
            status = "High Sales"

        # Format the percentage first, then use format_html
        formatted_percentage = f"{percentage:.1f}%"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({})</span>',
            color,
            formatted_percentage,
            status,
        )

    stock_utilization_badge.short_description = "Utilization"

    # Admin actions
    def reset_sold_stock(self, request, queryset):
        """Reset sold stock to 0 for selected records"""
        for stock in queryset:
            stock.sold_stock = 0.0
            stock.update_remaining_stock()
            stock.save()

        updated = queryset.count()
        self.message_user(
            request, f"Reset sold stock to 0 for {updated} stock record(s)."
        )

    reset_sold_stock.short_description = "Reset sold stock to 0"

    def update_remaining_stock(self, request, queryset):
        """Recalculate remaining stock for selected records"""
        for stock in queryset:
            stock.update_remaining_stock()
            stock.save()

        updated = queryset.count()
        self.message_user(request, f"Updated remaining stock for {updated} record(s).")

    update_remaining_stock.short_description = "Recalculate remaining stock"
