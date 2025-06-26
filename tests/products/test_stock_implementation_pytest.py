"""
Comprehensive pytest tests for Stock Data implementation
Tests models, GraphQL queries, mutations, and integration
"""

import pytest
from decimal import Decimal
from django.test import TransactionTestCase
from django.core.exceptions import ValidationError
from graphene.test import Client

from products.models import StockData, Product
from customers.models import Customer
from src.schemas import schema


# Fixtures for test data
@pytest.fixture
def stock_data_factory(db):
    """Factory for creating test stock data"""

    def create_stock_data(**kwargs):
        defaults = {
            "delivered_quantity": 1000.0,
            "price": Decimal("1.50"),
            "supplier": "Test Supplier",
            "cumulative_stock": 1000.0,
            "remaining_stock": 1000.0,
            "sold_stock": 0.0,
        }
        defaults.update(kwargs)
        return StockData.objects.create(**defaults)

    return create_stock_data


@pytest.fixture
def sample_stock_data(stock_data_factory):
    """Create sample stock data for testing"""
    return stock_data_factory(
        delivered_quantity=2000.0,
        price=Decimal("1.45"),
        supplier="Global Oil Ltd",
        cumulative_stock=2500.0,  # 500 from previous + 2000 new
        remaining_stock=1800.0,  # 2500 - 700 sold
        sold_stock=700.0,
    )


@pytest.fixture
def product_factory(db):
    """Factory for creating test products"""

    def create_product(**kwargs):
        defaults = {
            "name": "Test Product",
            "price": Decimal("45000.00"),
            "unit": 1,
            "sale_type": "retail",
        }
        defaults.update(kwargs)
        return Product.objects.create(**defaults)

    return create_product


@pytest.fixture
def customer_factory(db):
    """Factory for creating test customers"""

    def create_customer(**kwargs):
        defaults = {
            "name": "Test Customer",
            "email": "test@example.com",
            "phone": "+2348012345678",
            "type": "retail",
            "status": "active",
            "balance": Decimal("5000.00"),
            "credit_limit": Decimal("10000.00"),
        }
        defaults.update(kwargs)
        return Customer.objects.create(**defaults)

    return create_customer


@pytest.fixture
def graphql_client():
    """GraphQL test client"""
    return Client(schema)


@pytest.mark.django_db
class TestStockDataModel:
    """Test StockData model functionality"""

    def test_stock_data_creation(self, stock_data_factory):
        """Test basic stock data creation"""
        stock = stock_data_factory()

        assert stock.delivered_quantity == 1000.0
        assert stock.price == Decimal("1.50")
        assert stock.supplier == "Test Supplier"
        assert stock.cumulative_stock == 1000.0
        assert stock.remaining_stock == 1000.0
        assert stock.sold_stock == 0.0

    def test_stock_utilization_percentage(self, sample_stock_data):
        """Test stock utilization percentage calculation"""
        # sold_stock=700.0, cumulative_stock=2500.0
        expected_percentage = (700.0 / 2500.0) * 100  # 28%

        assert sample_stock_data.stock_utilization_percentage == expected_percentage

    def test_stock_utilization_percentage_zero_cumulative(self, stock_data_factory):
        """Test stock utilization when cumulative stock is zero"""
        stock = stock_data_factory(cumulative_stock=0.0)

        assert stock.stock_utilization_percentage == 0

    def test_previous_remaining_stock(self, sample_stock_data):
        """Test previous remaining stock calculation"""
        # cumulative_stock=2500.0, delivered_quantity=2000.0
        expected_previous = 2500.0 - 2000.0  # 500.0

        assert sample_stock_data.previous_remaining_stock == expected_previous

    def test_update_remaining_stock(self, sample_stock_data):
        """Test updating remaining stock"""
        sample_stock_data.sold_stock = 900.0
        sample_stock_data.update_remaining_stock()

        # cumulative_stock=2500.0, sold_stock=900.0
        expected_remaining = 2500.0 - 900.0  # 1600.0
        assert sample_stock_data.remaining_stock == expected_remaining

    def test_record_sale_success(self, sample_stock_data):
        """Test successful sale recording"""
        initial_sold = sample_stock_data.sold_stock
        initial_remaining = sample_stock_data.remaining_stock
        sale_quantity = 100.0

        sample_stock_data.record_sale(sale_quantity)

        assert sample_stock_data.sold_stock == initial_sold + sale_quantity
        assert sample_stock_data.remaining_stock == initial_remaining - sale_quantity

    def test_record_sale_insufficient_stock(self, sample_stock_data):
        """Test recording sale with insufficient stock"""
        # remaining_stock=1800.0, try to sell 2000.0
        with pytest.raises(ValueError, match="Cannot sell more than remaining stock"):
            sample_stock_data.record_sale(2000.0)

    def test_record_sale_exact_remaining_stock(self, sample_stock_data):
        """Test recording sale with exact remaining stock"""
        remaining = sample_stock_data.remaining_stock

        sample_stock_data.record_sale(remaining)

        assert sample_stock_data.remaining_stock == 0.0
        assert sample_stock_data.sold_stock == sample_stock_data.cumulative_stock

    def test_get_latest_remaining_stock_empty(self, db):
        """Test getting latest remaining stock when no data exists"""
        assert StockData.get_latest_remaining_stock() == 0.0

    def test_get_latest_remaining_stock_with_data(self, stock_data_factory):
        """Test getting latest remaining stock with data"""
        # Create multiple stock records
        stock1 = stock_data_factory(remaining_stock=500.0)
        stock2 = stock_data_factory(remaining_stock=1200.0)  # This should be latest

        assert StockData.get_latest_remaining_stock() == 1200.0

    def test_create_new_delivery(self, sample_stock_data):
        """Test creating new delivery with rolling stock"""
        # Get current latest remaining stock
        previous_remaining = StockData.get_latest_remaining_stock()

        new_delivery = StockData.create_new_delivery(
            delivered_quantity=1500.0, price=Decimal("1.60"), supplier="New Supplier Co"
        )

        assert new_delivery.delivered_quantity == 1500.0
        assert new_delivery.price == Decimal("1.60")
        assert new_delivery.supplier == "New Supplier Co"
        assert new_delivery.cumulative_stock == previous_remaining + 1500.0
        assert new_delivery.remaining_stock == previous_remaining + 1500.0
        assert new_delivery.sold_stock == 0.0

    def test_clean_validation_success(self, sample_stock_data):
        """Test model validation passes for valid data"""
        sample_stock_data.clean()  # Should not raise

    def test_clean_validation_failure(self, sample_stock_data):
        """Test model validation fails when sold > cumulative"""
        sample_stock_data.sold_stock = sample_stock_data.cumulative_stock + 100.0

        with pytest.raises(
            ValidationError, match="Sold stock cannot exceed cumulative stock"
        ):
            sample_stock_data.clean()

    def test_string_representation(self, sample_stock_data):
        """Test string representation"""
        expected = "Stock delivery of 2000.0 litres from Global Oil Ltd"
        assert str(sample_stock_data) == expected

    def test_model_ordering(self, stock_data_factory):
        """Test model ordering (newest first)"""
        stock1 = stock_data_factory(supplier="First")
        stock2 = stock_data_factory(supplier="Second")

        all_stock = list(StockData.objects.all())
        assert all_stock[0] == stock2  # Newest first
        assert all_stock[1] == stock1


@pytest.mark.django_db
class TestStockDataGraphQLQueries:
    """Test StockData GraphQL queries"""

    def test_stock_data_query_single(self, graphql_client, sample_stock_data):
        """Test querying single stock data by ID"""
        query = f"""
        query {{
            stockData(id: "{sample_stock_data.id}") {{
                id
                deliveredQuantity
                price
                supplier
                cumulativeStock
                remainingStock
                soldStock
                stockUtilizationPercentage
            }}
        }}
        """

        result = graphql_client.execute(query)

        assert not result.get("errors")
        data = result["data"]["stockData"]
        assert data["supplier"] == "Global Oil Ltd"
        assert float(data["deliveredQuantity"]) == 2000.0
        assert float(data["price"]) == 1.45

    def test_all_stock_data_query(self, graphql_client, stock_data_factory):
        """Test querying all stock data with pagination"""
        # Create multiple stock records
        stock_data_factory(supplier="Supplier A")
        stock_data_factory(supplier="Supplier B")
        stock_data_factory(supplier="Supplier C")

        query = """
        query {
            allStockData(first: 5) {
                edges {
                    node {
                        id
                        supplier
                        deliveredQuantity
                        remainingStock
                    }
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                }
            }
        }
        """

        result = graphql_client.execute(query)

        assert not result.get("errors")
        edges = result["data"]["allStockData"]["edges"]
        assert len(edges) == 3
        suppliers = [edge["node"]["supplier"] for edge in edges]
        assert "Supplier A" in suppliers
        assert "Supplier B" in suppliers
        assert "Supplier C" in suppliers

    def test_stock_data_by_supplier_query(self, graphql_client, stock_data_factory):
        """Test querying stock data by supplier"""
        stock_data_factory(supplier="ABC Supply Co")
        stock_data_factory(supplier="XYZ Petroleum")

        query = """
        query {
            stockDataBySupplier(supplier: "ABC") {
                id
                supplier
                deliveredQuantity
            }
        }
        """

        result = graphql_client.execute(query)

        assert not result.get("errors")
        data = result["data"]["stockDataBySupplier"]
        assert len(data) == 1
        assert data[0]["supplier"] == "ABC Supply Co"

    def test_latest_stock_deliveries_query(self, graphql_client, stock_data_factory):
        """Test querying latest stock deliveries"""
        stock_data_factory(supplier="Latest 1")
        stock_data_factory(supplier="Latest 2")
        stock_data_factory(supplier="Latest 3")

        query = """
        query {
            latestStockDeliveries(limit: 2) {
                id
                supplier
                deliveredQuantity
                createdAt
            }
        }
        """

        result = graphql_client.execute(query)

        assert not result.get("errors")
        data = result["data"]["latestStockDeliveries"]
        assert len(data) == 2
        # Should be ordered by creation date (newest first)
        assert data[0]["supplier"] == "Latest 3"
        assert data[1]["supplier"] == "Latest 2"

    def test_stock_data_filtering(self, graphql_client, stock_data_factory):
        """Test stock data filtering capabilities"""
        stock_data_factory(
            supplier="High Stock", remaining_stock=2000.0, price=Decimal("1.50")
        )
        stock_data_factory(
            supplier="Low Stock", remaining_stock=100.0, price=Decimal("1.60")
        )

        query = """
        query {
            allStockData(first: 10, remainingStock_Gte: 1000) {
                edges {
                    node {
                        supplier
                        remainingStock
                    }
                }
            }
        }
        """

        result = graphql_client.execute(query)

        assert not result.get("errors")
        edges = result["data"]["allStockData"]["edges"]
        assert len(edges) == 1
        assert edges[0]["node"]["supplier"] == "High Stock"


@pytest.mark.django_db
class TestStockDataGraphQLMutations:
    """Test StockData GraphQL mutations"""

    def test_create_stock_data_mutation(self, graphql_client):
        """Test creating stock data via mutation"""
        mutation = """
        mutation {
            addStockDelivery(
                deliveredQuantity: 1500.0
                price: "1.75"
                supplier: "New Supplier Ltd"
            ) {
                stockData {
                    id
                    supplier
                    deliveredQuantity
                    price
                    cumulativeStock
                    remainingStock
                }
                success
                message
            }
        }
        """

        result = graphql_client.execute(mutation)

        assert not result.get("errors")
        data = result["data"]["addStockDelivery"]
        assert data["success"] is True
        stock_data = data["stockData"]
        assert stock_data["supplier"] == "New Supplier Ltd"
        assert float(stock_data["deliveredQuantity"]) == 1500.0
        assert float(stock_data["price"]) == 1.75

    def test_create_stock_delivery_mutation(self, graphql_client, sample_stock_data):
        """Test creating stock delivery via mutation"""
        mutation = """
        mutation {
            addStockDelivery(
                deliveredQuantity: 2000.0
                price: "1.55"
                supplier: "Delivery Supplier"
            ) {
                stockData {
                    id
                    supplier
                    deliveredQuantity
                    cumulativeStock
                    remainingStock
                }
                success
                message
            }
        }
        """

        result = graphql_client.execute(mutation)

        assert not result.get("errors")
        data = result["data"]["addStockDelivery"]
        assert data["success"] is True
        stock_data = data["stockData"]
        assert stock_data["supplier"] == "Delivery Supplier"
        # Should use rolling stock calculation
        # Previous remaining (1800.0) + new delivery (2000.0) = 3800.0
        assert float(stock_data["cumulativeStock"]) == 3800.0

    def test_record_sale_mutation(self, graphql_client, sample_stock_data):
        """Test recording sale via mutation"""
        mutation = f"""
        mutation {{
            recordSale(input: {{
                stockDataId: "{sample_stock_data.id}"
                quantitySold: 200.0
            }}) {{
                stockData {{
                    id
                    remainingStock
                    soldStock
                    stockUtilizationPercentage
                }}
                success
                message
            }}
        }}
        """

        result = graphql_client.execute(mutation)

        assert not result.get("errors")
        data = result["data"]["recordSale"]
        assert data["success"] is True
        stock_data = data["stockData"]
        # Original: remaining=1800.0, sold=700.0
        # After sale: remaining=1600.0, sold=900.0
        assert float(stock_data["remainingStock"]) == 1600.0
        assert float(stock_data["soldStock"]) == 900.0

    def test_record_sale_insufficient_stock(self, graphql_client, sample_stock_data):
        """Test recording sale with insufficient stock"""
        mutation = f"""
        mutation {{
            recordSale(input: {{
                stockDataId: "{sample_stock_data.id}"
                quantitySold: 5000.0
            }}) {{
                stockData {{
                    id
                }}
                success
                message
            }}
        }}
        """

        result = graphql_client.execute(mutation)

        assert not result.get("errors")
        data = result["data"]["recordSale"]
        assert data["success"] is False
        assert "Cannot sell more than remaining stock" in data["message"]

    def test_update_stock_data_mutation(self, graphql_client, sample_stock_data):
        """Test updating stock data via mutation"""
        mutation = f"""
        mutation {{
            updateStockDelivery(input: {{
                id: "{sample_stock_data.id}"
                supplier: "Updated Supplier Name"
                price: "1.65"
            }}) {{
                stockData {{
                    id
                    supplier
                    price
                    deliveredQuantity
                }}
                success
                message
            }}
        }}
        """

        result = graphql_client.execute(mutation)

        assert not result.get("errors")
        data = result["data"]["updateStockDelivery"]
        assert data["success"] is True
        stock_data = data["stockData"]
        assert stock_data["supplier"] == "Updated Supplier Name"
        assert float(stock_data["price"]) == 1.65
        # Should not change delivered quantity
        assert float(stock_data["deliveredQuantity"]) == 2000.0

    def test_delete_stock_data_mutation(self, graphql_client, sample_stock_data):
        """Test deleting stock data via mutation"""
        stock_id = sample_stock_data.id

        mutation = f"""
        mutation {{
            deleteStockData(id: "{stock_id}") {{
                success
                message
            }}
        }}
        """

        result = graphql_client.execute(mutation)

        assert not result.get("errors")
        data = result["data"]["deleteStockData"]
        assert data["success"] is True

        # Verify deletion
        assert not StockData.objects.filter(id=stock_id).exists()


@pytest.mark.django_db
class TestStockIntegrationWithProducts:
    """Test stock integration with Product model"""

    def test_product_stock_calculation(self, product_factory, stock_data_factory):
        """Test product stock calculation from StockData"""
        # Create stock data with known remaining stock
        stock_data_factory(remaining_stock=6000.0)  # 6000L available

        # Create products with different units
        product_1_unit = product_factory(unit=1)  # 1 unit = 25L
        product_2_unit = product_factory(unit=2)  # 2 units = 50L
        product_4_unit = product_factory(unit=4)  # 4 units = 100L

        # Test stock calculations by calling the resolve method directly
        from products.schema.types.product_type import ProductType

        # Bind the method to the product instances and call
        product_type = ProductType()

        # 1 unit product: 6000 / 25 = 240 units
        stock_1 = product_type.resolve_stock.__func__(product_1_unit, None)
        assert stock_1 == 240

        # 2 unit product: 6000 / 50 = 120 units
        stock_2 = product_type.resolve_stock.__func__(product_2_unit, None)
        assert stock_2 == 120

        # 4 unit product: 6000 / 100 = 60 units
        stock_4 = product_type.resolve_stock.__func__(product_4_unit, None)
        assert stock_4 == 60

    def test_product_stock_zero_remaining(self, product_factory, stock_data_factory):
        """Test product stock when no stock remaining"""
        stock_data_factory(remaining_stock=0.0)
        product = product_factory(unit=1)

        from products.schema.types.product_type import ProductType

        product_type = ProductType()
        stock = product_type.resolve_stock.__func__(product, None)

        assert stock == 0

    def test_product_stock_no_stock_data(self, product_factory):
        """Test product stock when no StockData exists"""
        product = product_factory(unit=1)

        from products.schema.types.product_type import ProductType

        product_type = ProductType()
        stock = product_type.resolve_stock.__func__(product, None)

        assert stock == 0

    def test_product_stock_invalid_unit(self, product_factory, stock_data_factory):
        """Test product stock with invalid unit (zero or negative)"""
        stock_data_factory(remaining_stock=5000.0)
        product = product_factory(unit=0)

        from products.schema.types.product_type import ProductType

        product_type = ProductType()
        stock = product_type.resolve_stock.__func__(product, None)

        assert stock == 0


@pytest.mark.django_db
class TestStockDataConcurrency:
    """Test StockData concurrency and edge cases"""

    def test_concurrent_sales_simulation(self, stock_data_factory):
        """Simulate concurrent sales to test data integrity"""
        stock = stock_data_factory(
            cumulative_stock=1000.0, remaining_stock=1000.0, sold_stock=0.0
        )

        # Simulate multiple small sales
        sale_amounts = [100.0, 150.0, 200.0, 250.0]

        for amount in sale_amounts:
            stock.record_sale(amount)

        expected_total_sold = sum(sale_amounts)  # 700.0
        expected_remaining = 1000.0 - expected_total_sold  # 300.0

        assert stock.sold_stock == expected_total_sold
        assert stock.remaining_stock == expected_remaining

    def test_rolling_stock_chain(self, stock_data_factory):
        """Test chain of rolling stock deliveries"""
        # First delivery
        stock1 = stock_data_factory(
            delivered_quantity=1000.0,
            cumulative_stock=1000.0,
            remaining_stock=600.0,  # 400 sold
            sold_stock=400.0,
            supplier="Supplier 1",
        )

        # Second delivery (uses remaining from first)
        stock2 = StockData.create_new_delivery(
            delivered_quantity=800.0, price=Decimal("1.60"), supplier="Supplier 2"
        )
        stock2.save()

        # Should have: 600 (previous) + 800 (new) = 1400 cumulative
        assert stock2.cumulative_stock == 1400.0
        assert stock2.remaining_stock == 1400.0
        assert stock2.sold_stock == 0.0

        # Third delivery
        stock2.record_sale(300.0)  # Sell some from second batch
        stock2.save()

        stock3 = StockData.create_new_delivery(
            delivered_quantity=500.0, price=Decimal("1.55"), supplier="Supplier 3"
        )
        stock3.save()

        # Should have: 1100 (from stock2 after sale) + 500 (new) = 1600
        assert stock3.cumulative_stock == 1600.0

    def test_negative_values_validation(self, stock_data_factory):
        """Test that negative values are properly handled"""
        stock = stock_data_factory()

        # Test negative sale amount - should be caught by negative value check
        with pytest.raises(ValueError, match="Cannot record negative sale quantity"):
            stock.record_sale(-100.0)

        # Test creating stock with negative delivered quantity - should be prevented by model validators
        with pytest.raises(Exception):  # Could be ValidationError or IntegrityError
            bad_stock = StockData(
                delivered_quantity=-500.0,
                price=Decimal("1.50"),
                supplier="Bad Supplier",
                cumulative_stock=1000.0,
                remaining_stock=1000.0,
                sold_stock=0.0,
            )
            bad_stock.full_clean()  # This should trigger validation


# Performance and load testing
@pytest.mark.django_db
class TestStockDataPerformance:
    """Test StockData performance with larger datasets"""

    def test_large_dataset_query_performance(self, stock_data_factory):
        """Test query performance with larger dataset"""
        # Create 100 stock records
        for i in range(100):
            stock_data_factory(
                supplier=f"Supplier {i}",
                delivered_quantity=1000.0 + i,
                remaining_stock=800.0 + i,
            )

        # Test that get_latest_remaining_stock is efficient
        import time

        start_time = time.time()
        latest_stock = StockData.get_latest_remaining_stock()
        end_time = time.time()

        # Should complete quickly (less than 1 second)
        assert (end_time - start_time) < 1.0
        assert latest_stock > 0  # Should return the latest record's remaining stock

    def test_bulk_operations(self, stock_data_factory):
        """Test bulk operations on StockData"""
        # Create multiple records
        stocks = []
        for i in range(50):
            stock = stock_data_factory(
                supplier=f"Bulk Supplier {i}",
                delivered_quantity=1000.0 + i * 10,
                remaining_stock=900.0 + i * 10,
            )
            stocks.append(stock)

        # Test bulk update
        total_remaining = sum(stock.remaining_stock for stock in stocks)
        total_cumulative = sum(stock.cumulative_stock for stock in stocks)

        assert total_remaining > 0
        assert total_cumulative > 0
        assert len(stocks) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
