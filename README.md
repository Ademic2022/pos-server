# POS Server 🏪

A comprehensive Point of Sale (POS) backend system built with Django and GraphQL, designed for retail and wholesale businesses to manage sales, inventory, customers, and financial transactions.

## 🚀 Features

### Core Functionality
- **Sales Management**: Complete sales transaction processing with support for retail and wholesale operations
- **Customer Management**: Customer profiles with credit tracking, balance management, and transaction history
- **Product Management**: Comprehensive product catalog with stock tracking and inventory management
- **User Authentication**: Secure JWT-based authentication system with role-based access control

### Advanced Features
- **Credit System**: Customer credit management with overpayment and underpayment tracking
- **Stock Management**: Real-time inventory tracking with rolling stock calculations
- **Return Management**: Complete return workflow with approval system and automatic stock updates
- **Payment Processing**: Multiple payment methods (cash, transfer, credit card, part payment)
- **Analytics & Reporting**: Comprehensive sales statistics and financial reporting

### Technical Features
- **GraphQL API**: Modern GraphQL endpoint with comprehensive queries and mutations
- **Real-time Updates**: Live inventory and sales tracking
- **Data Integrity**: Transaction-based operations ensuring data consistency
- **Extensible Architecture**: Modular design for easy feature additions

## 🛠️ Technology Stack

- **Backend Framework**: Django 5.2.3
- **API Layer**: GraphQL (Graphene-Django)
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Authentication**: JWT tokens with django-graphql-jwt
- **Testing**: Pytest with Factory Boy
- **CORS**: Django CORS headers for frontend integration

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pos-server
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - GraphQL endpoint: `http://localhost:8000/graphql/`
   - Django Admin: `http://localhost:8000/admin/`

## 🏗️ Project Structure

```
pos-server/
├── accounts/          # User authentication and management
├── customers/         # Customer management system
├── products/          # Product catalog and inventory
├── sales/            # Sales transactions and payments
├── shared/           # Shared utilities and types
├── src/              # Project configuration
├── tests/            # Test suite
├── manage.py         # Django management script
└── requirements.txt  # Project dependencies
```

## 📊 Database Schema

### Core Models
- **User**: Authentication and user management
- **Customer**: Customer profiles with credit tracking
- **Product**: Product catalog with pricing
- **Sale**: Sales transactions with items and payments
- **StockData**: Inventory tracking with rolling calculations
- **Return**: Return management with approval workflow

### Key Relationships
- Customers can have multiple sales and credit transactions
- Sales contain multiple sale items and payments
- Products track stock levels and movements
- Returns are linked to original sales for stock management

## 🔧 API Usage

### GraphQL Endpoint
The main GraphQL endpoint is available at `/graphql/` with the following capabilities:

#### Authentication
```graphql
mutation {
  tokenAuth(username: "your_username", password: "your_password") {
    token
    refreshToken
  }
}
```

#### Sales Operations
```graphql
mutation {
  createSale(input: {
    customerId: "1"
    items: [
      {productId: "1", quantity: 2, unitPrice: "10.00"}
    ]
    payments: {method: "cash", amount: "20.00", balance: "0.00"}
  }) {
    success
    message
    sale {
      transactionId
      total
    }
  }
}
```

#### Query Sales Statistics
```graphql
query {
  salesStats(dateFrom: "2024-01-01", dateTo: "2024-12-31") {
    totalSales
    totalTransactions
    averageSaleValue
    customerDebtIncurred {
      value
      count
    }
  }
}
```

## 🧪 Testing

Run the test suite using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_sales.py
```

## 🔐 Security Features

- JWT-based authentication with token refresh
- CORS protection for cross-origin requests
- SQL injection protection through Django ORM
- Input validation and sanitization
- Role-based access control

## 🚀 Deployment

### Production Considerations
1. **Database**: Switch to PostgreSQL for production
2. **Environment Variables**: Use environment-specific configurations
3. **Static Files**: Configure static file serving
4. **Security**: Update SECRET_KEY and security settings
5. **CORS**: Configure specific allowed origins

### Environment Variables
Create a `.env` file for production settings:
```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/dbname
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 📈 Performance Features

- **Optimized Queries**: Efficient database queries with select_related/prefetch_related
- **Pagination**: Built-in pagination for large datasets
- **Filtering**: Advanced filtering capabilities for all major entities
- **Caching**: Ready for Redis integration for improved performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation in the `/docs` folder

## 🔄 Changelog

### Version 1.0.0
- Initial release with core POS functionality
- Customer and product management
- Sales transaction processing
- Credit and payment system
- Return management workflow
- Comprehensive GraphQL API

---

**Built with ❤️ using Django and GraphQL**