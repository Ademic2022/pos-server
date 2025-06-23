from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from products.choices import SaleType


# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.0"))]
    )
    unit = models.PositiveIntegerField(default=0)
    sale_type = models.CharField(
        max_length=20, choices=SaleType.choices, default=SaleType.RETAIL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sale_type", "unit"]
        indexes = [models.Index(fields=["sale_type"])]

    def __str__(self):
        return f"{self.name} ({self.get_sale_type_display()})"


class StockData(models.Model):
    """Model to track stock deliveries and inventory levels in a rolling stock system"""

    delivered_quantity = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Total litres/units delivered in this stock batch",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.0"))],
        help_text="Price per unit of stock",
    )
    supplier = models.CharField(max_length=200, help_text="Stock supplier name")
    cumulative_stock = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Total cumulative stock (previous remaining + new delivery)",
    )
    remaining_stock = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Current stock remaining after sales (cumulative_stock - sold_stock)",
    )
    sold_stock = models.FloatField(
        validators=[MinValueValidator(0.0)],
        default=0.0,
        help_text="Total litres/units sold from current stock",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["supplier"]),
        ]
        verbose_name = "Stock Data"
        verbose_name_plural = "Stock Data"

    def __str__(self):
        supplier_part = f" from {self.supplier}" if self.supplier else ""
        return f"Stock delivery of {self.delivered_quantity} litres{supplier_part}"

    @property
    def stock_utilization_percentage(self):
        """Calculate what percentage of cumulative stock has been sold"""
        if self.cumulative_stock > 0:
            return (self.sold_stock / self.cumulative_stock) * 100
        return 0

    @property
    def previous_remaining_stock(self):
        """Calculate what the previous remaining stock was before this delivery"""
        return self.cumulative_stock - self.delivered_quantity

    def update_remaining_stock(self):
        """Update remaining_stock based on cumulative_stock and sold_stock"""
        self.remaining_stock = self.cumulative_stock - self.sold_stock

    def record_sale(self, quantity_sold):
        """Record a sale and update remaining stock"""
        if quantity_sold > self.remaining_stock:
            raise ValueError("Cannot sell more than remaining stock")

        self.sold_stock += quantity_sold
        self.remaining_stock = self.cumulative_stock - self.sold_stock

    @classmethod
    def create_new_delivery(
        cls, delivered_quantity, price, supplier, previous_remaining=0.0
    ):
        """Create a new stock delivery with proper rolling stock calculation"""
        cumulative_stock = previous_remaining + delivered_quantity
        remaining_stock = cumulative_stock  # No sales yet for new delivery

        return cls(
            delivered_quantity=delivered_quantity,
            price=price,
            supplier=supplier,
            cumulative_stock=cumulative_stock,
            remaining_stock=remaining_stock,
            sold_stock=0.0,
        )

    def clean(self):
        """Validate that sold stock doesn't exceed cumulative stock"""
        from django.core.exceptions import ValidationError

        if self.sold_stock > self.cumulative_stock:
            raise ValidationError("Sold stock cannot exceed cumulative stock")
