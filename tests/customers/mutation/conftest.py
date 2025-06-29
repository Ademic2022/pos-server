import pytest
from tests.factories import CustomerFactory
from decimal import Decimal


@pytest.fixture
def customer_data():
    """Sample customer data for mutation testing"""
    return {
        "name": "Test Customer",
        "email": "test@example.com",
        "phone": "+1234567890",
        "address": "123 Test Street",
        "type": "retail",
        "status": "active",
        "creditLimit": "500.00",
        "notes": "Test customer for mutations",
    }


@pytest.fixture
def existing_customer(db):
    """Create an existing customer for update/delete tests"""
    return CustomerFactory(
        name="Existing Customer",
        email="existing@example.com",
        phone="+1987654321",
        type="wholesale",
        status="active",
        balance=Decimal("100.00"),
        credit_limit=Decimal("1000.00"),
    )
