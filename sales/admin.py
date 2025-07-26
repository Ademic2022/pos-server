from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal
from sales.models import Sale, SaleItem, Payment, CustomerCredit


class SaleItemInline(admin.TabularInline):
    """Inline admin for sale items"""

    model = SaleItem
    extra = 0
    readonly_fields = ("total_price_display",)
    fields = ("product", "quantity", "unit_price", "total_price", "total_price_display")

    def total_price_display(self, obj):
        """Display total price with formatting"""
        if obj.total_price:
            total_val = float(obj.total_price)
            return format_html(
                '<strong style="color: green;">₦{}</strong>', f"{total_val:,.2f}"
            )
        return "₦0.00"

    total_price_display.short_description = "Formatted Total"


class PaymentInline(admin.TabularInline):
    """Inline admin for payments"""

    model = Payment
    extra = 0
    readonly_fields = ("amount_display", "created_at")
    fields = ("method", "amount", "balance", "amount_display", "created_at")

    def amount_display(self, obj):
        """Display payment amount with formatting"""
        if obj.amount:
            amount_val = float(obj.amount)
            return format_html(
                '<strong style="color: blue;">₦{}</strong>', f"{amount_val:,.2f}"
            )
        return "₦0.00"

    amount_display.short_description = "Formatted Amount"


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """Admin interface for Sale model"""

    # List display configuration
    list_display = [
        "transaction_id",
        "customer_link",
        "sale_type_badge",
        "subtotal_display",
        "discount_display",
        "total_display",
        "balance_status",
        "payment_status",
        "items_count",
        "created_at",
    ]

    # List filters
    list_filter = [
        "sale_type",
        "created_at",
        "updated_at",
        ("customer", admin.RelatedOnlyFieldListFilter),
    ]

    # Search functionality
    search_fields = [
        "transaction_id",
        "customer__name",
        "customer__phone",
        "customer__email",
    ]

    # Ordering
    ordering = ["-created_at"]

    # Read-only fields
    readonly_fields = [
        "transaction_id",
        "subtotal_display",
        "total_display",
        "balance_display",
        "amount_due_display",
        "profit_margin",
        "created_at",
        "updated_at",
    ]

    # Fieldsets for organized form layout
    fieldsets = (
        ("Sale Information", {"fields": ("transaction_id", "customer", "sale_type")}),
        (
            "Financial Details",
            {
                "fields": (
                    ("subtotal", "subtotal_display"),
                    "discount",
                    ("total", "total_display"),
                    ("credit_applied", "balance", "balance_display"),
                    ("amount_due", "amount_due_display"),
                ),
                "classes": ("wide",),
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

    # Inlines
    inlines = [SaleItemInline, PaymentInline]

    # Actions
    actions = ["mark_as_paid", "calculate_totals", "export_selected_sales"]

    def customer_link(self, obj):
        """Display customer as clickable link"""
        if obj.customer:
            url = reverse("admin:customers_customer_change", args=[obj.customer.pk])
            return format_html('<a href="{}">{}</a>', url, obj.customer.name)
        return "Walk-in Customer"

    customer_link.short_description = "Customer"
    customer_link.admin_order_field = "customer__name"

    def sale_type_badge(self, obj):
        """Display sale type with color coding"""
        colors = {
            "retail": "green",
            "wholesale": "blue",
        }
        color = colors.get(obj.sale_type, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_sale_type_display(),
        )

    sale_type_badge.short_description = "Sale Type"
    sale_type_badge.admin_order_field = "sale_type"

    def subtotal_display(self, obj):
        """Display subtotal with formatting"""
        subtotal_val = float(obj.subtotal or 0)
        return format_html("<strong>₦{}</strong>", f"{subtotal_val:,.2f}")

    subtotal_display.short_description = "Subtotal"
    subtotal_display.admin_order_field = "subtotal"

    def discount_display(self, obj):
        """Display discount with formatting"""
        if obj.discount and obj.discount > 0:
            discount_val = float(obj.discount)
            return format_html(
                '<span style="color: orange;">-₦{}</span>', f"{discount_val:,.2f}"
            )
        return "₦0.00"

    discount_display.short_description = "Discount"
    discount_display.admin_order_field = "discount"

    def total_display(self, obj):
        """Display total with formatting"""
        total_val = float(obj.total or 0)
        return format_html(
            '<strong style="color: green; font-size: 14px;">₦{}</strong>',
            f"{total_val:,.2f}",
        )

    total_display.short_description = "Total"
    total_display.admin_order_field = "total"

    def balance_display(self, obj):
        """Display balance with formatting"""
        balance = float(obj.balance or 0)
        color = "red" if balance > 0 else "green"
        return format_html(
            '<span style="color: {}; font-weight: bold;">₦{}</span>',
            color,
            f"{balance:,.2f}",
        )

    balance_display.short_description = "Balance"

    def amount_due_display(self, obj):
        """Display amount due with formatting"""
        amount_due = float(obj.amount_due or 0)
        color = "red" if amount_due > 0 else "green"
        return format_html(
            '<span style="color: {}; font-weight: bold;">₦{}</span>',
            color,
            f"{amount_due:,.2f}",
        )

    amount_due_display.short_description = "Amount Due"

    def balance_status(self, obj):
        """Display balance status badge"""
        balance = obj.balance or 0
        if balance == 0:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
                "PAID",
            )
        else:
            return format_html(
                '<span style="background-color: red; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
                "PENDING",
            )

    balance_status.short_description = "Status"

    def payment_status(self, obj):
        """Display payment completion percentage"""
        if obj.total and obj.total > 0:
            payments_total = sum(
                payment.amount for payment in obj.payments.all() if payment.amount
            )
            percentage = float((payments_total / obj.total) * 100)
            color = (
                "green"
                if percentage >= 100
                else "orange" if percentage >= 50 else "red"
            )
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}%</span>',
                color,
                f"{percentage:.1f}",
            )
        return "0%"

    payment_status.short_description = "Payment %"

    def items_count(self, obj):
        """Display number of items in sale"""
        count = obj.items.count()
        return format_html('<span style="">{} items</span>', count)

    items_count.short_description = "Items"

    def profit_margin(self, obj):
        """Calculate and display profit margin"""
        # This would require cost price data from products
        return "N/A"

    profit_margin.short_description = "Profit Margin"

    # Admin actions
    def mark_as_paid(self, request, queryset):
        """Mark selected sales as fully paid"""
        for sale in queryset:
            sale.balance = Decimal("0.00")
            sale.save()
        updated = queryset.count()
        self.message_user(request, f"{updated} sale(s) marked as paid.")

    mark_as_paid.short_description = "Mark selected sales as paid"

    def calculate_totals(self, request, queryset):
        """Recalculate totals for selected sales"""
        for sale in queryset:
            sale.calculate_totals()
        updated = queryset.count()
        self.message_user(request, f"Recalculated totals for {updated} sale(s).")

    calculate_totals.short_description = "Recalculate totals"


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    """Admin interface for SaleItem model"""

    list_display = [
        "sale_link",
        "product_link",
        "quantity",
        "unit_price_display",
        "total_price_display",
        "profit_display",
    ]

    list_filter = [
        ("sale", admin.RelatedOnlyFieldListFilter),
        ("product", admin.RelatedOnlyFieldListFilter),
        "sale__created_at",
    ]

    search_fields = [
        "sale__transaction_id",
        "product__name",
        "product__code",
    ]

    readonly_fields = ["total_price_display", "profit_display"]

    def sale_link(self, obj):
        """Display sale as clickable link"""
        url = reverse("admin:sales_sale_change", args=[obj.sale.pk])
        return format_html('<a href="{}">{}</a>', url, obj.sale.transaction_id)

    sale_link.short_description = "Sale"
    sale_link.admin_order_field = "sale__transaction_id"

    def product_link(self, obj):
        """Display product as clickable link"""
        url = reverse("admin:products_product_change", args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)

    product_link.short_description = "Product"
    product_link.admin_order_field = "product__name"

    def unit_price_display(self, obj):
        """Display unit price with formatting"""
        price_val = float(obj.unit_price or 0)
        return format_html("₦{}", f"{price_val:,.2f}")

    unit_price_display.short_description = "Unit Price"
    unit_price_display.admin_order_field = "unit_price"

    def total_price_display(self, obj):
        """Display total price with formatting"""
        total_val = float(obj.total_price or 0)
        return format_html(
            '<strong style="color: green;">₦{}</strong>', f"{total_val:,.2f}"
        )

    total_price_display.short_description = "Total Price"

    def profit_display(self, obj):
        """Display profit (would need cost price from product)"""
        return "N/A"

    profit_display.short_description = "Profit"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model"""

    list_display = [
        "sale_link",
        "method_badge",
        "amount_display",
        "customer_name",
        "created_at",
    ]

    list_filter = [
        "method",
        "created_at",
        ("sale", admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        "sale__transaction_id",
        "sale__customer__name",
    ]

    readonly_fields = ["amount_display", "created_at", "updated_at"]

    fieldsets = (
        ("Payment Details", {"fields": ("sale", "method", "amount", "amount_display")}),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def sale_link(self, obj):
        """Display sale as clickable link"""
        url = reverse("admin:sales_sale_change", args=[obj.sale.pk])
        return format_html('<a href="{}">{}</a>', url, obj.sale.transaction_id)

    sale_link.short_description = "Sale"
    sale_link.admin_order_field = "sale__transaction_id"

    def method_badge(self, obj):
        """Display payment method with color coding"""
        colors = {
            "cash": "green",
            "transfer": "blue",
            "credit": "orange",
            "part_payment": "purple",
        }
        color = colors.get(obj.method, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_method_display(),
        )

    method_badge.short_description = "Method"
    method_badge.admin_order_field = "method"

    def amount_display(self, obj):
        """Display amount with formatting"""
        amount_val = float(obj.amount or 0)
        return format_html(
            '<strong style="color: blue;">₦{}</strong>', f"{amount_val:,.2f}"
        )

    amount_display.short_description = "Amount"
    amount_display.admin_order_field = "amount"

    def customer_name(self, obj):
        """Display customer name"""
        if obj.sale and obj.sale.customer:
            return obj.sale.customer.name
        return "Walk-in"

    customer_name.short_description = "Customer"


@admin.register(CustomerCredit)
class CustomerCreditAdmin(admin.ModelAdmin):
    """Admin interface for CustomerCredit model"""

    list_display = [
        "customer_link",
        "transaction_type_badge",
        "amount_display",
        "balance_after_display",
        "sale_link",
        "created_at",
    ]

    list_filter = [
        "transaction_type",
        "created_at",
        ("customer", admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        "customer__name",
        "customer__phone",
        "description",
        "sale__transaction_id",
    ]

    readonly_fields = [
        "amount_display",
        "balance_after_display",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Credit Transaction",
            {"fields": ("customer", "transaction_type", "amount", "amount_display")},
        ),
        (
            "Balance & References",
            {
                "fields": (
                    "balance_after",
                    "balance_after_display",
                    "sale",
                    "description",
                )
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

    def customer_link(self, obj):
        """Display customer as clickable link"""
        url = reverse("admin:customers_customer_change", args=[obj.customer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.customer.name)

    customer_link.short_description = "Customer"
    customer_link.admin_order_field = "customer__name"

    def transaction_type_badge(self, obj):
        """Display transaction type with color coding"""
        colors = {
            "credit_added": "green",
            "credit_used": "red",
            "credit_refund": "blue",
            "credit_earned": "darkgreen",
            "debt_incurred": "darkred",
        }
        color = colors.get(obj.transaction_type, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_transaction_type_display(),
        )

    transaction_type_badge.short_description = "Type"
    transaction_type_badge.admin_order_field = "transaction_type"

    def amount_display(self, obj):
        """Display amount with formatting and sign"""
        amount = float(obj.amount or 0)
        if obj.transaction_type in ["credit_used", "debt_incurred"]:
            return format_html(
                '<span style="color: red;">-₦{}</span>', f"{amount:,.2f}"
            )
        else:
            return format_html(
                '<span style="color: green;">+₦{}</span>', f"{amount:,.2f}"
            )

    amount_display.short_description = "Amount"
    amount_display.admin_order_field = "amount"

    def balance_after_display(self, obj):
        """Display balance after with formatting"""
        balance = float(obj.balance_after or 0)
        color = "green" if balance > 0 else "red" if balance < 0 else "gray"
        return format_html(
            '<strong style="color: {};">₦{}</strong>', color, f"{balance:,.2f}"
        )

    balance_after_display.short_description = "Balance After"
    balance_after_display.admin_order_field = "balance_after"

    def sale_link(self, obj):
        """Display related sale as clickable link"""
        if obj.sale:
            url = reverse("admin:sales_sale_change", args=[obj.sale.pk])
            return format_html('<a href="{}">{}</a>', url, obj.sale.transaction_id)
        return "-"

    sale_link.short_description = "Related Sale"
