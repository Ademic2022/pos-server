# Test Organization Summary

## Test Structure

The tests are now organized in the `tests/` directory with the following structure:

```
tests/
├── __init__.py
├── conftest.py               # Pytest fixtures
├── factories.py              # Factory Boy factories for test data
├── test_infrastructure.py    # Tests for test infrastructure
├── utils.py                  # Test utilities
└── accounts/
    ├── __init__.py
    ├── conftest.py           # Account-specific fixtures
    ├── test_models.py        # Account model tests
    ├── test_integration.py   # Integration tests
    ├── mutation/
    │   ├── __init__.py
    │   └── test_accounts_mutations.py  # GraphQL mutation tests
    └── query/
        ├── __init__.py
        └── test_accounts_queries.py    # GraphQL query tests
```

## Available Test Files

### 1. Model Tests (`tests/accounts/test_models.py`)
- **TestUserModel**: Tests for User model functionality
  - User creation
  - String representations
  - Manager methods (create_user, create_superuser)
  - Relationships with roles
- **TestRoleModel**: Tests for Role model
  - Role creation and relationships
  - Permissions handling
- **TestUserSessionModel**: Tests for UserSession model
- **TestActivityLogModel**: Tests for ActivityLog model

### 2. GraphQL Query Tests (`tests/accounts/query/test_accounts_queries.py`)
- Authentication required tests
- Users query tests
- Single user query tests
- Roles query tests
- Activity logs query tests
- Current user query tests
- Permission checking tests

### 3. GraphQL Mutation Tests (`tests/accounts/mutation/test_accounts_mutations.py`)
- User registration tests
- Authentication (login/logout) tests
- Token verification tests
- Password change tests
- Account update tests

### 4. Integration Tests (`tests/accounts/test_integration.py`)
- Complete user flows (registration → login)
- Role and permission flows
- Activity logging tests
- Session tracking tests
- Database constraint tests
- Security tests

### 5. Test Infrastructure (`tests/test_infrastructure.py`)
- Factory testing
- Fixture testing
- GraphQL client testing

## Test Factories

Located in `tests/factories.py`:

- **UserFactory**: Creates test users with customizable attributes
- **SuperUserFactory**: Creates superusers
- **RoleFactory**: Creates roles with permissions
- **UserSessionFactory**: Creates user sessions
- **ActivityLogFactory**: Creates activity logs

## Running Tests

### Using Django Test Runner (Recommended)

```bash
# Run all tests
python manage.py test

# Run specific test modules
python manage.py test tests.accounts.test_models
python manage.py test tests.accounts.query.test_accounts_queries
python manage.py test tests.accounts.mutation.test_accounts_mutations
python manage.py test tests.accounts.test_integration

# Run with verbosity
python manage.py test tests.accounts.test_models --verbosity=2

# Run specific test class
python manage.py test tests.accounts.test_models.TestUserModel

# Run specific test method
python manage.py test tests.accounts.test_models.TestUserModel.test_user_creation
```

### Using Pytest (Configuration in Progress)

Note: Pytest configuration is still being finalized. For now, use Django's test runner.

```bash
# When pytest is working:
pytest tests/accounts/test_models.py
pytest tests/accounts/ -v
pytest -m unit  # Run only unit tests
pytest -m integration  # Run only integration tests
```

## Test Data Generation

The factories use Faker to generate realistic test data:

```python
# Create a user
user = UserFactory()

# Create a user with specific attributes
user = UserFactory(username="testuser", email="test@example.com")

# Create multiple users
users = UserFactory.create_batch(5)

# Create user with role
role = RoleFactory(name="Manager")
user = UserFactory(role=role)
```

## GraphQL Testing Utilities

Located in `tests/utils.py`:

- `execute_graphql_query()`: Helper for executing GraphQL queries
- `assert_graphql_success()`: Assert successful GraphQL responses
- `assert_graphql_error()`: Assert GraphQL error responses
- `GraphQLTestMixin`: Mixin class for GraphQL testing

## Test Examples

### Testing a GraphQL Query
```python
def test_users_query(self):
    query = '''
        query {
            users {
                edges {
                    node {
                        id
                        username
                    }
                }
            }
        }
    '''
    # Test with authenticated request
    result = self.execute_query(query, user=self.staff_user)
    self.assert_query_success(result)
```

### Testing a GraphQL Mutation
```python
def test_user_registration(self):
    mutation = '''
        mutation RegisterUser($input: RegisterInput!) {
            register(input: $input) {
                success
                errors
            }
        }
    '''
    variables = {
        'input': {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
    }
    result = self.execute_query(mutation, variables=variables)
    # Check result...
```

## Current Status

✅ **Working Tests:**
- Model tests (20 tests passing)
- Test infrastructure with Django test runner
- Factory Boy integration
- Test organization structure

🔄 **In Progress:**
- Pytest configuration
- GraphQL query/mutation tests execution
- Integration test refinement

## Next Steps

1. Fix pytest-django configuration
2. Run and validate GraphQL tests
3. Add more edge case tests
4. Add performance tests
5. Add API documentation tests
