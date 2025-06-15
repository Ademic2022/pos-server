from django.db import models


class AccountStatusChoices(models.TextChoices):
    ACTIVE = "MALE", "Male"
    INACTIVE = "FEMALE", "Female"
    SUSPENDED = "ANY", "Any"


class ActionChoices(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    VIEW = "view", "View"
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    SALE = "sale", "Sale"
    PAYMENT = "payment", "Payment"
    RETURN = "return", "Return"
