from decimal import Decimal
from django.db import models
from django.core.validators import RegexValidator
from accounts.models import NULL, User
from customers.choices import CustomerTypes, StatusChoices


class Customer(models.Model):
    """
    Customer model for managing customer information in the POS system
    """

    # Basic Information
    name = models.CharField(max_length=100)
    email = models.EmailField(**NULL)

    # Phone validation
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    phone = models.CharField(
        validators=[phone_regex], max_length=17, help_text="Customer's phone number"
    )

    # Address Information
    address = models.TextField(**NULL)

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
        default=Decimal("0.00"),
    )
    credit_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total_purchases = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    # Tracking Information
    last_purchase = models.DateTimeField(**NULL)
    notes = models.TextField(**NULL)

    # Audit Fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        **NULL,
        related_name="customers_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        ordering = ["-last_purchase"]

    def __str__(self):
        return f"{self.name} ({self.type})"

    @property
    def join_date(self):
        """Return the join date as created_at for frontend compatibility"""
        return self.created_at

    def available_credit(self):
        """Calculate available credit"""
        # Ensure both values are Decimal objects to avoid type errors
        credit_limit = (
            Decimal(str(self.credit_limit)) if self.credit_limit else Decimal("0.00")
        )
        balance = Decimal(str(self.balance)) if self.balance else Decimal("0.00")
        return max(Decimal("0.00"), credit_limit + balance)

    @property
    def is_credit_available(self):
        """Check if customer has available credit"""
        return self.available_credit() > Decimal("0.00")

    def can_make_purchase(self, amount):
        """Check if customer can make a purchase of given amount"""
        amount = Decimal(str(amount))

        if self.status != "active":
            return False

        if self.type == "retail":
            return True  # Retail customers pay immediately

        return (self.balance + amount) <= self.credit_limit

    def add_purchase(self, amount, purchase_date=None):
        """Add a purchase to customer's record"""
        from django.utils import timezone

        amount = Decimal(str(amount))

        self.balance += amount
        self.total_purchases += amount
        self.last_purchase = purchase_date or timezone.now()
        self.save(
            update_fields=["balance", "total_purchases", "last_purchase", "updated_at"]
        )

    def make_payment(self, amount):
        """Record a payment from customer"""
        self.balance = max(Decimal("0.00"), self.balance - amount)
        self.save(update_fields=["balance", "updated_at"])

    def get_current_credit_balance(self):
        """Get current credit balance from CustomerCredit transactions"""
        # Import here to avoid circular import
        from sales.models import CustomerCredit

        latest_credit = (
            CustomerCredit.objects.filter(customer=self).order_by("-created_at").first()
        )

        if latest_credit:
            return Decimal(str(latest_credit.balance_after))
        else:
            # If no credit transactions, use the customer balance field
            return Decimal(str(self.balance or "0.00"))

    def has_available_credit(self):
        """Check if customer has positive credit balance"""
        return self.get_current_credit_balance() > Decimal("0.00")
