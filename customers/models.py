from django.db import models
from django.core.validators import RegexValidator
from accounts.models import User
from customers.choices import CustomerTypes, StatusChoices


class Customer(models.Model):
    """
    Customer model for managing customer information in the POS system
    """

    # Basic Information
    name = models.CharField(max_length=100, help_text="Customer's full name")
    email = models.EmailField(
        blank=True, null=True, help_text="Customer's email address"
    )

    # Phone validation
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    phone = models.CharField(
        validators=[phone_regex], max_length=17, help_text="Customer's phone number"
    )

    # Address Information
    address = models.TextField(blank=True, null=True, help_text="Customer's address")

    # Customer Type and Status
    type = models.CharField(
        max_length=10,
        choices=CustomerTypes.choices,
        default=CustomerTypes.RETAIL,
        help_text="Customer type (retail or wholesale)",
    )
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )

    # Financial Information
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Customer's current balance",
    )
    credit_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Customer's credit limit",
    )
    total_purchases = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Total amount of purchases",
    )

    # Tracking Information
    last_purchase = models.DateTimeField(
        blank=True, null=True, help_text="Date of last purchase"
    )
    notes = models.TextField(
        blank=True, null=True, help_text="Additional notes about the customer"
    )

    # Audit Fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers_created",
        help_text="User who created this customer",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.type})"

    @property
    def join_date(self):
        """Return the join date as created_at for frontend compatibility"""
        return self.created_at

    @property
    def available_credit(self):
        """Calculate available credit"""
        return max(0, self.credit_limit - self.balance)

    @property
    def is_credit_available(self):
        """Check if customer has available credit"""
        return self.available_credit > 0

    def can_make_purchase(self, amount):
        """Check if customer can make a purchase of given amount"""
        if self.status != "active":
            return False

        if self.type == "retail":
            return True  # Retail customers pay immediately

        # For wholesale customers, check credit limit
        return (self.balance + amount) <= self.credit_limit

    def add_purchase(self, amount, purchase_date=None):
        """Add a purchase to customer's record"""
        from django.utils import timezone

        self.balance += amount
        self.total_purchases += amount
        self.last_purchase = purchase_date or timezone.now()
        self.save(
            update_fields=["balance", "total_purchases", "last_purchase", "updated_at"]
        )

    def make_payment(self, amount):
        """Record a payment from customer"""
        self.balance = max(0, self.balance - amount)
        self.save(update_fields=["balance", "updated_at"])
