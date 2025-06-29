from django.db import models


class SaleTypeChoices(models.TextChoices):
    RETAIL = "retail", "Retail"
    WHOLESALE = "wholesale", "Wholesale"


class PaymentMethodChoices(models.TextChoices):
    CASH = "cash", "Cash"
    TRANSFER = "transfer", "Bank Transfer"
    CREDIT = "credit", "Credit"
    PART_PAYMENT = "part_payment", "Part Payment"


class TransactionTypeChoices(models.TextChoices):
    CREDIT_ADDED = "credit_added", "Credit Added"
    CREDIT_USED = "credit_used", "Credit Used"
    CREDIT_REFUND = "credit_refund", "Credit Refund"
    CREDIT_EARNED = "credit_earned", "Credit Earned (Overpayment)"
    DEBT_INCURRED = "debt_incurred", "Debt Incurred (Underpayment)"
