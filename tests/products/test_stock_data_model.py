import pytest
from django.test import TestCase
from decimal import Decimal
from products.models import StockData


class TestStockDataModel(TestCase):
    """Test StockData model functionality"""

    def setUp(self):
        """Set up test data"""
        self.stock_data = StockData.objects.create(
            delivered_quantity=1000.0,
            price=Decimal("1.50"),
            supplier="Test Supplier",
            cumulative_stock=1200.0,  # 200 from previous + 1000 new
            remaining_stock=800.0,  # 1200 - 400 sold
            sold_stock=400.0,
        )

    def test_stock_data_creation(self):
        """Test StockData instance creation"""
        self.assertEqual(self.stock_data.delivered_quantity, 1000.0)
        self.assertEqual(self.stock_data.price, Decimal("1.50"))
        self.assertEqual(self.stock_data.supplier, "Test Supplier")
        self.assertEqual(self.stock_data.cumulative_stock, 1200.0)
        self.assertEqual(self.stock_data.remaining_stock, 800.0)
        self.assertEqual(self.stock_data.sold_stock, 400.0)

    def test_stock_utilization_percentage(self):
        """Test stock utilization percentage calculation"""
        expected_percentage = (400.0 / 1200.0) * 100  # 33.33%
        self.assertAlmostEqual(
            self.stock_data.stock_utilization_percentage, expected_percentage, places=2
        )

    def test_previous_remaining_stock(self):
        """Test previous remaining stock calculation"""
        expected_previous = 1200.0 - 1000.0  # 200.0
        self.assertEqual(self.stock_data.previous_remaining_stock, expected_previous)

    def test_update_remaining_stock(self):
        """Test updating remaining stock"""
        self.stock_data.sold_stock = 500.0
        self.stock_data.update_remaining_stock()

        expected_remaining = 1200.0 - 500.0  # 700.0
        self.assertEqual(self.stock_data.remaining_stock, expected_remaining)

    def test_record_sale(self):
        """Test recording a sale"""
        initial_sold = self.stock_data.sold_stock
        initial_remaining = self.stock_data.remaining_stock
        sale_quantity = 100.0

        self.stock_data.record_sale(sale_quantity)

        self.assertEqual(self.stock_data.sold_stock, initial_sold + sale_quantity)
        self.assertEqual(
            self.stock_data.remaining_stock, initial_remaining - sale_quantity
        )

    def test_record_sale_insufficient_stock(self):
        """Test recording sale with insufficient stock"""
        with self.assertRaises(ValueError):
            self.stock_data.record_sale(1000.0)  # More than remaining stock

    def test_create_new_delivery(self):
        """Test creating new delivery with rolling stock"""
        # Get the current remaining stock (should be 800.0 from setup)
        previous_remaining = StockData.get_latest_remaining_stock()

        new_delivery = StockData.create_new_delivery(
            delivered_quantity=500.0,
            price=Decimal("1.60"),
            supplier="New Test Supplier",
        )

        self.assertEqual(new_delivery.delivered_quantity, 500.0)
        self.assertEqual(new_delivery.price, Decimal("1.60"))
        self.assertEqual(new_delivery.supplier, "New Test Supplier")
        # cumulative_stock should be previous_remaining + delivered_quantity
        expected_cumulative = previous_remaining + 500.0
        self.assertEqual(new_delivery.cumulative_stock, expected_cumulative)
        self.assertEqual(
            new_delivery.remaining_stock, expected_cumulative
        )  # No sales yet
        self.assertEqual(new_delivery.sold_stock, 0.0)

    def test_str_representation(self):
        """Test string representation"""
        expected_str = "Stock delivery of 1000.0 litres from Test Supplier"
        self.assertEqual(str(self.stock_data), expected_str)

    def test_meta_ordering(self):
        """Test model ordering"""
        # Create another stock data with different date
        newer_stock = StockData.objects.create(
            delivered_quantity=800.0,
            price=Decimal("1.55"),
            supplier="Newer Supplier",
            cumulative_stock=800.0,
            remaining_stock=800.0,
            sold_stock=0.0,
        )

        # Check ordering (newest first)
        all_stock = list(StockData.objects.all())
        self.assertEqual(all_stock[0], newer_stock)
        self.assertEqual(all_stock[1], self.stock_data)
