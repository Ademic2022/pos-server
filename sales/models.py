from decimal import Decimal
import uuid
from django.db import models
from accounts.models import NULL
from customers.models import Customer
from products.models import Product
from sales.choices import PaymentMethodChoices, SaleTypeChoices, TransactionTypeChoices


class Sale(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    sale_type = models.CharField(
        max_length=20, choices=SaleTypeChoices.choices, default=SaleTypeChoices.RETAIL
    )
    transaction_id = models.CharField(max_length=50, unique=True)

    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    discount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    credit_applied = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    amount_due = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate transaction ID like #SE44156525
            self.transaction_id = f"#SE{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        customer_name = self.customer.name if self.customer else "Walk-in"
        return f"{self.transaction_id} - {customer_name} - ₦{self.subtotal:,.2f}"

    def calculate_totals(self):
        """Recalculate all totals based on sale items"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.total_amount = self.subtotal - self.discount
        self.amount_due = max(0, self.total_amount - self.credit_applied)
        self.save()


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Payment(models.Model):
    sale = models.ForeignKey(Sale, related_name="payments", on_delete=models.CASCADE)
    method = models.CharField(max_length=20, choices=PaymentMethodChoices.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.method} - ₦{self.amount}"


class CustomerCredit(models.Model):
    """Track customer credit transactions"""

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="credit_transactions"
    )
    transaction_type = models.CharField(
        max_length=15, choices=TransactionTypeChoices.choices
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)

    # Optional relation to sale if credit was used/earned from a sale
    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, **NULL)

    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.name} - {self.get_transaction_type_display()} - ₦{self.amount:,.2f}"
