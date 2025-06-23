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
