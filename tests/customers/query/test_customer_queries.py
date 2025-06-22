from decimal import Decimal
from src.schemas import schema
from tests.factories import CustomerFactory


class TestCustomerQueries:
    """Test customer GraphQL queries"""

    def test_single_customer_query(
        self, db, user_with_token, sample_customers, graphql_request_factory
    ):
        """Test querying a single customer by ID"""
        customer = sample_customers[0]

        query = """
        query($id: ID!) {
            customer(id: $id) {
                id
                name
                email
                phone
                type
                status
                balance
                creditLimit
            }
        }
        """

        request = graphql_request_factory(user_with_token)
        result = schema.execute(
            query, variables={"id": str(customer.id)}, context=request
        )

        assert result.errors is None
        # Note: ID is returned as a Relay Global ID (base64 encoded)
        assert result.data["customer"]["id"] is not None
        assert result.data["customer"]["name"] == customer.name
        assert result.data["customer"]["email"] == customer.email
        assert result.data["customer"]["phone"] == customer.phone
        # GraphQL enums are returned in uppercase
        assert result.data["customer"]["type"] == customer.type.upper()
        assert result.data["customer"]["status"] == customer.status.upper()

    def test_single_customer_not_found(
        self, db, user_with_token, graphql_request_factory
    ):
        """Test querying a customer that doesn't exist"""
        query = """
        query($id: ID!) {
            customer(id: $id) {
                id
                name
            }
        }
        """

        request = graphql_request_factory(user_with_token)
        result = schema.execute(query, variables={"id": "999999"}, context=request)

        assert result.errors is None
        assert result.data["customer"] is None

    def test_customers_connection_basic(
        self, db, user_with_token, sample_customers, graphql_request_factory
    ):
        """Test basic customers connection query"""
        query = """
        query {
            customers(first: 10) {
                edges {
                    node {
                        id
                        name
                        email
                        type
                        status
                    }
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
        """

        request = graphql_request_factory(user_with_token)
        result = schema.execute(query, context=request)

        assert result.errors is None
        assert len(result.data["customers"]["edges"]) == len(sample_customers)
        assert result.data["customers"]["pageInfo"]["hasNextPage"] is False

    def test_customers_pagination(
        self, db, user_with_token, many_customers, graphql_request_factory
    ):
        """Test pagination with many customers"""
        query = """
        query($first: Int, $after: String) {
            customers(first: $first, after: $after) {
                edges {
                    node {
                        id
                        name
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
        """

        # First page
        request = graphql_request_factory(user_with_token)
        result = schema.execute(query, variables={"first": 10}, context=request)

        assert result.errors is None
        assert len(result.data["customers"]["edges"]) == 10
        assert result.data["customers"]["pageInfo"]["hasNextPage"] is True

        # Get next page
        end_cursor = result.data["customers"]["pageInfo"]["endCursor"]
        result_page2 = schema.execute(
            query, variables={"first": 10, "after": end_cursor}, context=request
        )

        assert result_page2.errors is None
        assert len(result_page2.data["customers"]["edges"]) == 10
        assert result_page2.data["customers"]["pageInfo"]["hasNextPage"] is True

    def test_customers_filter_by_name(
        self, db, user_with_token, sample_customers, graphql_request_factory
    ):
        """Test filtering customers by name"""
        query = """
        query($nameFilter: String) {
            customers(name_Icontains: $nameFilter) {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
        """

        request = graphql_request_factory(user_with_token)
        result = schema.execute(
            query, variables={"nameFilter": "john"}, context=request
        )

        assert result.errors is None
        found_customers = result.data["customers"]["edges"]
        assert len(found_customers) == 2  # John Doe and Bob Johnson
        names = [edge["node"]["name"] for edge in found_customers]
        assert "John Doe" in names
        assert "Bob Johnson" in names

    def test_customers_filter_by_type(
        self, db, user_with_token, sample_customers, graphql_request_factory
    ):
        """Test filtering customers by type"""
        query = """
        query($type: CustomerTypeEnum) {
            customers(type: $type) {
                edges {
                    node {
                        id
                        name
                        type
                    }
                }
            }
        }
        """

        request = graphql_request_factory(user_with_token)
        result = schema.execute(
            query,
            variables={"type": "WHOLESALE"},  # Use GraphQL enum value
            context=request,
        )

        assert result.errors is None
        found_customers = result.data["customers"]["edges"]
        assert len(found_customers) == 2  # Jane Smith and Alice Brown
        for edge in found_customers:
            assert edge["node"]["type"] == "WHOLESALE"

    def test_customers_filter_by_status(
        self, db, user_with_token, sample_customers, graphql_request_factory
    ):
        """Test filtering customers by status"""
        query = """
        query($status: CustomerStatusEnum) {
            customers(status: $status) {
                edges {
                    node {
                        id
                        name
                        status
                    }
                }
            }
        }
        """

        request = graphql_request_factory(user_with_token)
        result = schema.execute(
            query,
            variables={"status": "ACTIVE"},  # Use GraphQL enum value
            context=request,
        )

        assert result.errors is None
        found_customers = result.data["customers"]["edges"]
        assert len(found_customers) == 2  # John Doe and Jane Smith
        for edge in found_customers:
            assert edge["node"]["status"] == "ACTIVE"

    def test_customers_filter_by_balance_range(
        self, db, user_with_token, sample_customers, graphql_request_factory
    ):
        """Test filtering customers by balance range"""
        query = """
        query($minBalance: Decimal, $maxBalance: Decimal) {
            customers(balance_Gte: $minBalance, balance_Lte: $maxBalance) {
                edges {
                    node {
                        id
                        name
                        balance
                    }
                }
            }
        }
        """

        request = graphql_request_factory(user_with_token)
        result = schema.execute(
            query,
            variables={"minBalance": "50.00", "maxBalance": "200.00"},
            context=request,
        )

        assert result.errors is None
        found_customers = result.data["customers"]["edges"]
        assert len(found_customers) == 2  # John Doe (100.00) and Alice Brown (75.50)

    def test_customers_filter_by_email(
        self, db, user_with_token, sample_customers, graphql_request_factory
    ):
        """Test filtering customers by email"""
        query = """
        query($emailFilter: String) {
            customers(email_Icontains: $emailFilter) {
                edges {
                    node {
                        id
                        name
                        email
                    }
                }
            }
        }
        """

        request = graphql_request_factory(user_with_token)
        result = schema.execute(
            query, variables={"emailFilter": "smith"}, context=request
        )

        assert result.errors is None
        found_customers = result.data["customers"]["edges"]
        assert len(found_customers) == 1
        assert found_customers[0]["node"]["name"] == "Jane Smith"

    def test_customers_multiple_filters(
        self, db, user_with_token, sample_customers, graphql_request_factory
    ):
        """Test combining multiple filters"""
        query = """
        query($type: CustomerTypeEnum, $status: CustomerStatusEnum) {
            customers(type: $type, status: $status) {
                edges {
                    node {
                        id
                        name
                        type
                        status
                    }
                }
            }
        }
        """

        request = graphql_request_factory(user_with_token)
        result = schema.execute(
            query,
            variables={"type": "RETAIL", "status": "ACTIVE"},  # Use GraphQL enum values
            context=request,
        )

        assert result.errors is None
        found_customers = result.data["customers"]["edges"]
        assert len(found_customers) == 1  # Only John Doe
        assert found_customers[0]["node"]["name"] == "John Doe"

    def test_customer_stats(
        self, db, user_with_token, sample_customers, graphql_request_factory
    ):
        """Test customer statistics query"""
        query = """
        query {
            customerStats {
                totalCustomers
                retailCustomers
                wholesaleCustomers
                activeCustomers
                inactiveCustomers
                blockedCustomers
                totalCreditIssued
                totalOutstandingBalance
            }
        }
        """

        request = graphql_request_factory(user_with_token)
        result = schema.execute(query, context=request)

        assert result.errors is None
        stats = result.data["customerStats"]
        assert stats["totalCustomers"] == 4
        assert stats["retailCustomers"] == 2
        assert stats["wholesaleCustomers"] == 2
        assert stats["activeCustomers"] == 2
        assert stats["inactiveCustomers"] == 1
        assert stats["blockedCustomers"] == 1

    def test_unauthenticated_access(self, db):
        """Test that unauthenticated users cannot access customer data"""
        query = """
        query {
            customers(first: 5) {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
        """

        result = schema.execute(query)

        assert result.errors is not None
        assert "'NoneType' object has no attribute 'user'" in str(result.errors[0])

    def test_customers_complex_filter_scenario(
        self, db, user_with_token, graphql_request_factory
    ):
        """Test a complex real-world filtering scenario"""
        # Create specific customers for this test
        CustomerFactory(
            name="Premium Customer A",
            type="wholesale",
            status="active",
            balance=Decimal("1000.00"),
            credit_limit=Decimal("5000.00"),
        )
        CustomerFactory(
            name="Premium Customer B",
            type="wholesale",
            status="active",
            balance=Decimal("500.00"),
            credit_limit=Decimal("3000.00"),
        )
        CustomerFactory(
            name="Regular Customer",
            type="retail",
            status="active",
            balance=Decimal("50.00"),
            credit_limit=Decimal("500.00"),
        )

        query = """
        query {
            customers(
                type: WHOLESALE,
                status: ACTIVE,
                balance_Gte: "400.00"
            ) {
                edges {
                    node {
                        id
                        name
                        type
                        status
                        balance
                        creditLimit
                    }
                }
            }
        }
        """

        request = graphql_request_factory(user_with_token)
        result = schema.execute(query, context=request)

        assert result.errors is None
        found_customers = result.data["customers"]["edges"]
        assert len(found_customers) == 2  # Both premium customers

        for edge in found_customers:
            customer = edge["node"]
            assert customer["type"] == "WHOLESALE"
            assert customer["status"] == "ACTIVE"
            assert float(customer["balance"]) >= 400.00
