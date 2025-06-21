import pytest
from tests.factories import CustomerFactory
from decimal import Decimal


@pytest.fixture
def sample_customers(db):
    """Create sample customers for testing"""
    customers = [
        CustomerFactory(
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            type="retail",
            status="active",
            balance=Decimal("100.00"),
            credit_limit=Decimal("500.00"),
        ),
        CustomerFactory(
            name="Jane Smith",
            email="jane.smith@example.com",
            phone="+1987654321",
            type="wholesale",
            status="active",
            balance=Decimal("250.00"),
            credit_limit=Decimal("1000.00"),
        ),
        CustomerFactory(
            name="Bob Johnson",
            email="bob.johnson@example.com",
            phone="+1555123456",
            type="retail",
            status="inactive",
            balance=Decimal("0.00"),
            credit_limit=Decimal("200.00"),
        ),
        CustomerFactory(
            name="Alice Brown",
            email="alice.brown@example.com",
            phone="+1666789012",
            type="wholesale",
            status="blocked",
            balance=Decimal("75.50"),
            credit_limit=Decimal("0.00"),
        ),
    ]
    return customers


@pytest.fixture
def many_customers(db):
    """Create many customers for pagination testing"""
    return CustomerFactory.create_batch(25)
