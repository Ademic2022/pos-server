from django.db import models


class CustomerTypes(models.TextChoices):
    RETAIL = "retail", "Retail"
    WHOLESALE = "wholesale", "Wholesale"


class StatusChoices(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    BLOCKED = "blocked", "Blocked"
