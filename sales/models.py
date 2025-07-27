from decimal import Decimal
import uuid
from django.db import models
from django.utils import timezone
from accounts.models import NULL
from customers.models import Customer
from products.models import Product
from sales.choices import (
    PaymentMethodChoices,
    SaleTypeChoices,
    TransactionTypeChoices,
    ReturnStatusChoices,
)


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


class Return(models.Model):
    """Track customer returns"""

    return_id = models.CharField(max_length=50, unique=True)
    original_sale = models.ForeignKey(
        Sale, on_delete=models.CASCADE, related_name="returns"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="returns"
    )

    status = models.CharField(
        max_length=15,
        choices=ReturnStatusChoices.choices,
        default=ReturnStatusChoices.PENDING,
    )

    reason = models.TextField(help_text="Reason for return")
    total_refund_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    # Who approved/rejected the return
    approved_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, **NULL)
    approved_at = models.DateTimeField(**NULL)
    approval_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.return_id:
            # Generate return ID like #RT44156525
            self.return_id = f"#RT{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.return_id} - {self.customer.name} - {self.get_status_display()}"

    def approve_return(self, approved_by_user, notes=""):
        """Approve the return and update stock"""
        from products.models import StockData

        if self.status != ReturnStatusChoices.PENDING:
            raise ValueError("Can only approve pending returns")

        self.status = ReturnStatusChoices.APPROVED
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.approval_notes = notes

        # Update stock for each returned item
        for return_item in self.items.all():
            # Add returned quantity back to stock
            latest_stock_record = StockData.objects.order_by("-created_at").first()
            if latest_stock_record:
                # Calculate litres to add back based on product unit
                litres_per_unit = 25.0  # Same as in CreateSale mutation
                returned_litres = (
                    return_item.product.unit * litres_per_unit * return_item.quantity
                )

                # Add back to stock by reducing sold_stock
                latest_stock_record.sold_stock = max(
                    0, latest_stock_record.sold_stock - returned_litres
                )
                latest_stock_record.remaining_stock = (
                    latest_stock_record.cumulative_stock
                    - latest_stock_record.sold_stock
                )
                latest_stock_record.save()

        # Create customer credit for refund amount
        if self.total_refund_amount > 0:
            current_balance = self.customer.get_current_credit_balance()
            new_balance = current_balance + self.total_refund_amount

            CustomerCredit.objects.create(
                customer=self.customer,
                transaction_type="credit_refund",
                amount=self.total_refund_amount,
                balance_after=new_balance,
                description=f"Refund for return {self.return_id}",
            )

            # Update customer balance
            self.customer.balance = new_balance
            self.customer.save()

        self.status = ReturnStatusChoices.COMPLETED
        self.save()

    def reject_return(self, rejected_by_user, notes=""):
        """Reject the return"""
        if self.status != ReturnStatusChoices.PENDING:
            raise ValueError("Can only reject pending returns")

        self.status = ReturnStatusChoices.REJECTED
        self.approved_by = rejected_by_user
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()


class ReturnItem(models.Model):
    """Individual items being returned"""

    return_request = models.ForeignKey(
        Return, related_name="items", on_delete=models.CASCADE
    )
    original_sale_item = models.ForeignKey(SaleItem, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)

    quantity = models.PositiveIntegerField(help_text="Quantity being returned")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Return {self.quantity}x {self.product.name}"

    def clean(self):
        from django.core.exceptions import ValidationError

        # Ensure return quantity doesn't exceed original quantity
        if self.quantity > self.original_sale_item.quantity:
            raise ValidationError(
                "Return quantity cannot exceed original purchase quantity"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
