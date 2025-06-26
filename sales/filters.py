"""
Django filters for Sales models
"""
import django_filters
from django.db.models import Q
from sales.models import Sale, SaleItem, Payment, CustomerCredit


class SaleFilter(django_filters.FilterSet):
    """Filter for Sale model"""
    
    customer = django_filters.NumberFilter(field_name='customer__id')
    customer_name = django_filters.CharFilter(
        field_name='customer__name', 
        lookup_expr='icontains'
    )
    sale_type = django_filters.ChoiceFilter(
        field_name='sale_type',
        choices=[('retail', 'Retail'), ('wholesale', 'Wholesale')]
    )
    transaction_id = django_filters.CharFilter(
        field_name='transaction_id',
        lookup_expr='icontains'
    )
    
    # Date filters
    created_at = django_filters.DateFromToRangeFilter()
    created_at_date = django_filters.DateFilter(field_name='created_at__date')
    created_at_month = django_filters.NumberFilter(field_name='created_at__month')
    created_at_year = django_filters.NumberFilter(field_name='created_at__year')
    
    # Amount filters
    total = django_filters.RangeFilter()
    total_min = django_filters.NumberFilter(field_name='total', lookup_expr='gte')
    total_max = django_filters.NumberFilter(field_name='total', lookup_expr='lte')
    
    subtotal = django_filters.RangeFilter()
    discount = django_filters.RangeFilter()
    amount_due = django_filters.RangeFilter()
    
    # Status filters
    has_amount_due = django_filters.BooleanFilter(
        method='filter_has_amount_due'
    )
    has_discount = django_filters.BooleanFilter(
        method='filter_has_discount'
    )
    has_credit_applied = django_filters.BooleanFilter(
        method='filter_has_credit_applied'
    )
    
    # Search across multiple fields
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Sale
        fields = {
            'id': ['exact'],
            'subtotal': ['exact', 'gte', 'lte'],
            'discount': ['exact', 'gte', 'lte'],
            'total': ['exact', 'gte', 'lte'],
            'balance': ['exact', 'gte', 'lte'],
            'credit_applied': ['exact', 'gte', 'lte'],
            'amount_due': ['exact', 'gte', 'lte'],
            'created_at': ['exact', 'date', 'month', 'year'],
            'updated_at': ['exact', 'date', 'month', 'year'],
        }
    
    def filter_has_amount_due(self, queryset, name, value):
        """Filter sales with or without amount due"""
        if value:
            return queryset.filter(amount_due__gt=0)
        return queryset.filter(amount_due=0)
    
    def filter_has_discount(self, queryset, name, value):
        """Filter sales with or without discount"""
        if value:
            return queryset.filter(discount__gt=0)
        return queryset.filter(discount=0)
    
    def filter_has_credit_applied(self, queryset, name, value):
        """Filter sales with or without credit applied"""
        if value:
            return queryset.filter(credit_applied__gt=0)
        return queryset.filter(credit_applied=0)
    
    def filter_search(self, queryset, name, value):
        """Search across transaction_id and customer name"""
        return queryset.filter(
            Q(transaction_id__icontains=value) |
            Q(customer__name__icontains=value) |
            Q(customer__phone__icontains=value)
        )


class SaleItemFilter(django_filters.FilterSet):
    """Filter for SaleItem model"""
    
    sale = django_filters.NumberFilter(field_name='sale__id')
    product = django_filters.NumberFilter(field_name='product__id')
    product_name = django_filters.CharFilter(
        field_name='product__name',
        lookup_expr='icontains'
    )
    
    quantity = django_filters.RangeFilter()
    unit_price = django_filters.RangeFilter()
    total_price = django_filters.RangeFilter()
    
    class Meta:
        model = SaleItem
        fields = {
            'id': ['exact'],
            'quantity': ['exact', 'gte', 'lte'],
            'unit_price': ['exact', 'gte', 'lte'],
            'total_price': ['exact', 'gte', 'lte'],
        }


class PaymentFilter(django_filters.FilterSet):
    """Filter for Payment model"""
    
    sale = django_filters.NumberFilter(field_name='sale__id')
    method = django_filters.ChoiceFilter(
        field_name='method',
        choices=[
            ('cash', 'Cash'),
            ('transfer', 'Bank Transfer'),
            ('credit', 'Credit'),
            ('part_payment', 'Part Payment')
        ]
    )
    
    amount = django_filters.RangeFilter()
    created_at = django_filters.DateFromToRangeFilter()
    
    class Meta:
        model = Payment
        fields = {
            'id': ['exact'],
            'amount': ['exact', 'gte', 'lte'],
            'created_at': ['exact', 'date', 'month', 'year'],
            'updated_at': ['exact', 'date', 'month', 'year'],
        }


class CustomerCreditFilter(django_filters.FilterSet):
    """Filter for CustomerCredit model"""
    
    customer = django_filters.NumberFilter(field_name='customer__id')
    customer_name = django_filters.CharFilter(
        field_name='customer__name',
        lookup_expr='icontains'
    )
    transaction_type = django_filters.ChoiceFilter(
        field_name='transaction_type',
        choices=[
            ('credit_added', 'Credit Added'),
            ('credit_used', 'Credit Used'),
            ('credit_refund', 'Credit Refund')
        ]
    )
    
    sale = django_filters.NumberFilter(field_name='sale__id')
    amount = django_filters.RangeFilter()
    balance_after = django_filters.RangeFilter()
    created_at = django_filters.DateFromToRangeFilter()
    
    description = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = CustomerCredit
        fields = {
            'id': ['exact'],
            'amount': ['exact', 'gte', 'lte'],
            'balance_after': ['exact', 'gte', 'lte'],
            'created_at': ['exact', 'date', 'month', 'year'],
            'updated_at': ['exact', 'date', 'month', 'year'],
        }
