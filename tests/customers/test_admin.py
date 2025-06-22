import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from customers.models import Customer
from customers.admin import CustomerAdmin
from tests.factories import CustomerFactory, UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestCustomerAdmin:
    """Test cases for Customer admin interface"""

    def test_customer_admin_registered(self):
        """Test that CustomerAdmin is properly registered"""
        assert admin.site.is_registered(Customer)
        assert isinstance(admin.site._registry[Customer], CustomerAdmin)

    def test_status_badge_method(self):
        """Test status badge display method"""
        admin_instance = CustomerAdmin(Customer, admin.site)

        # Test active status
        customer = CustomerFactory(status="active")
        badge_html = admin_instance.status_badge(customer)
        assert "green" in badge_html
        assert "Active" in badge_html

        # Test blocked status
        customer = CustomerFactory(status="blocked")
        badge_html = admin_instance.status_badge(customer)
        assert "red" in badge_html
        assert "Blocked" in badge_html

    def test_available_credit_display_method(self):
        """Test available credit display method"""
        admin_instance = CustomerAdmin(Customer, admin.site)

        # Test customer with good credit
        customer = CustomerFactory(balance=100, credit_limit=1000)
        credit_html = admin_instance.available_credit_display(customer)
        assert "green" in credit_html
        assert "$900.00" in credit_html

        # Test customer with no credit
        customer = CustomerFactory(balance=1000, credit_limit=1000)
        credit_html = admin_instance.available_credit_display(customer)
        assert "red" in credit_html
        assert "$0.00" in credit_html

    def test_save_model_sets_created_by(self, rf):
        """Test that save_model sets created_by for new customers"""
        user = UserFactory()
        request = rf.get("/")
        request.user = user

        admin_instance = CustomerAdmin(Customer, admin.site)
        customer = Customer(name="Test Customer", phone="+1234567890")

        # Simulate creating new customer (change=False)
        admin_instance.save_model(request, customer, None, change=False)

        assert customer.created_by == user

    def test_admin_actions(self, rf):
        """Test admin actions for bulk status updates"""
        from django.contrib.messages.storage.fallback import FallbackStorage

        user = UserFactory()
        request = rf.get("/")
        request.user = user

        # Add message storage to request
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))

        admin_instance = CustomerAdmin(Customer, admin.site)
        customers = CustomerFactory.create_batch(3, status="inactive")
        queryset = Customer.objects.filter(id__in=[c.id for c in customers])

        # Test mark as active action
        admin_instance.mark_as_active(request, queryset)

        # Refresh from database
        for customer in customers:
            customer.refresh_from_db()
            assert customer.status == "active"

    def test_list_display_fields(self):
        """Test that all list_display fields are accessible"""
        admin_instance = CustomerAdmin(Customer, admin.site)
        customer = CustomerFactory()

        # Test that all list_display methods work
        assert admin_instance.status_badge(customer) is not None
        assert admin_instance.available_credit_display(customer) is not None

    def test_search_functionality(self):
        """Test that search fields are properly configured"""
        admin_instance = CustomerAdmin(Customer, admin.site)

        # Verify search fields are set
        expected_search_fields = ("name", "email", "phone", "address")
        assert admin_instance.search_fields == expected_search_fields

    def test_list_filters(self):
        """Test that list filters are properly configured"""
        admin_instance = CustomerAdmin(Customer, admin.site)

        expected_filters = (
            "type",
            "status",
            "created_at",
            "last_purchase",
            "created_by",
        )
        assert admin_instance.list_filter == expected_filters
