from django.db import models


class SaleType(models.TextChoices):
    WHOLESALE = "wholesale", "Wholesale"
    RETAIL = "retail", "Retail"
