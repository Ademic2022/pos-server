"""
GraphQL mutations for Sales
"""

import traceback
import graphene
from decimal import Decimal
from django.db import transaction
from sales.models import Sale, SaleItem, Payment, CustomerCredit, Return, ReturnItem
from customers.models import Customer
from products.models import Product
from sales.schema.types.sale_types import (
    ReturnType,
    SaleType,
    PaymentType,
    CustomerCreditType,
)
from sales.schema.inputs.sale_inputs import (
    ApproveReturnInput,
    CreateReturnInput,
    CreateSaleInput,
    RejectReturnInput,
    UpdateSaleInput,
    AddPaymentInput,
    CustomerCreditInput,
)


class CreateSale(graphene.Mutation):
    """Create a new sale with items and payments"""

    class Arguments:
        input = CreateSaleInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    sale = graphene.Field(SaleType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        try:
            # Get customer if provided
            customer = None
            if input.customer_id:
                try:
                    customer = Customer.objects.get(id=input.customer_id)
                except Customer.DoesNotExist:
                    return CreateSale(
                        success=False,
                        message="Customer not found",
                        errors=["Customer not found"],
                    )

            # Create the sale
            sale = Sale.objects.create(
                customer=customer,
                sale_type=input.sale_type.value,  # Use .value to get the string value
                discount=input.discount,
                # Don't set credit_applied here - we'll calculate it automatically
            )

            # Add sale items
            subtotal = Decimal("0.00")
            for item_input in input.items:
                try:
                    product = Product.objects.get(id=item_input.product_id)

                    # Check stock availability using the GraphQL stock calculation
                    from products.models import StockData

                    latest_remaining_stock = StockData.get_latest_remaining_stock()

                    # Calculate available stock for this product
                    if latest_remaining_stock <= 0 or product.unit <= 0:
                        available_stock = 0
                    else:
                        litres_per_unit = 25.0
                        total_litres_needed = product.unit * litres_per_unit
                        available_stock = int(
                            latest_remaining_stock / total_litres_needed
                        )

                    if available_stock < item_input.quantity:
                        raise ValueError(
                            f"Insufficient stock for {product.name}. Available: {available_stock}, Requested: {item_input.quantity}"
                        )

                    # Create sale item
                    total_price = item_input.unit_price * item_input.quantity
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=item_input.quantity,
                        unit_price=item_input.unit_price,
                        total_price=total_price,
                    )

                    # Update stock by recording sale in StockData
                    litres_sold = product.unit * 25.0 * item_input.quantity
                    latest_stock_record = StockData.objects.order_by(
                        "-created_at"
                    ).first()
                    if latest_stock_record:
                        latest_stock_record.record_sale(litres_sold)
                        latest_stock_record.save()

                    subtotal += total_price

                except Product.DoesNotExist:
                    raise ValueError(f"Product not found: {item_input.product_id}")

            # Update sale totals
            sale.subtotal = subtotal
            sale.total = subtotal - sale.discount
            sale.save()

            # Add payment and calculate total payments
            total_payments = Decimal("0.00")
            Payment.objects.create(
                sale=sale,
                method=str(input.payment.method.value),  # Convert enum to string
                amount=input.payment.amount,
                balance=input.payment.balance,
            )
            total_payments = input.payment.amount

            # AUTOMATIC CREDIT HANDLING LOGIC
            credit_applied = Decimal("0.00")
            current_customer_balance = Decimal("0.00")

            if customer:
                # Get customer's current credit balance at start
                current_customer_balance = customer.get_current_credit_balance()
                print("Current customer balance:", current_customer_balance)

                # ALWAYS apply available credit first (if customer has any)
                if current_customer_balance > 0:
                    # Apply credit up to the sale total
                    credit_applied = min(current_customer_balance, sale.total)

                    # Update customer balance after credit use
                    current_customer_balance = current_customer_balance - credit_applied

                    # Create credit_used transaction
                    CustomerCredit.objects.create(
                        customer=customer,
                        transaction_type="credit_used",
                        amount=credit_applied,
                        balance_after=current_customer_balance,
                        sale=sale,
                        description=f"Credit applied to sale {sale.transaction_id}",
                    )

                    # Update customer balance
                    customer.balance = current_customer_balance
                    customer.save()

                # Calculate net amount owed after credit is applied
                amount_owed_after_credit = sale.total - credit_applied
                print("Amount owed after credit:", amount_owed_after_credit)
                print("Total payments received:", total_payments)

                # Calculate final balance after payments
                final_balance = amount_owed_after_credit - total_payments

                if final_balance > 0:
                    # Customer still owes money - record as debt
                    current_customer_balance = current_customer_balance - final_balance

                    CustomerCredit.objects.create(
                        customer=customer,
                        transaction_type="debt_incurred",
                        amount=final_balance,
                        balance_after=current_customer_balance,
                        sale=sale,
                        description=f"Debt incurred from underpayment on sale {sale.transaction_id}",
                    )

                    # Update customer balance
                    customer.balance = current_customer_balance
                    customer.save()

                elif final_balance < 0:
                    # Customer overpaid - record the overpayment as credit earned
                    overpayment = abs(final_balance)
                    current_customer_balance = current_customer_balance + overpayment

                    # Determine description based on whether customer had existing credit
                    if credit_applied > 0:
                        description = f"Additional payment made on sale {sale.transaction_id} (customer had existing credit)"
                    else:
                        description = f"Credit earned from overpayment on sale {sale.transaction_id}"

                    CustomerCredit.objects.create(
                        customer=customer,
                        transaction_type="credit_earned",
                        amount=overpayment,
                        balance_after=current_customer_balance,
                        sale=sale,
                        description=description,
                    )

                    # Update customer balance
                    customer.balance = current_customer_balance
                    customer.save()

                # Update customer's total_purchases and last_purchase
                customer.total_purchases += sale.total
                customer.last_purchase = sale.created_at
                customer.save(
                    update_fields=["total_purchases", "last_purchase", "updated_at"]
                )

            # Update sale with final calculated values
            sale.credit_applied = credit_applied
            amount_after_credit_and_payments = (
                sale.total - credit_applied - total_payments
            )
            sale.amount_due = Decimal(max(0, amount_after_credit_and_payments))
            sale.balance = Decimal(sale.amount_due)  # Balance is what's still owed
            sale.save()

            print(
                f"Final calculation: Sale total={sale.total}, Credit applied={credit_applied}, Payments={total_payments}, Amount due={sale.amount_due}"
            )

            return CreateSale(
                success=True,
                message=f"Sale {sale.transaction_id} created successfully",
                sale=sale,
            )

        except Exception as e:
            traceback.print_exc()  # Log the exception for debugging
            return CreateSale(
                success=False,
                message=f"Failed to create sale: {str(e)}",
                errors=[str(e)],
            )


class UpdateSale(graphene.Mutation):
    """Update an existing sale"""

    class Arguments:
        input = UpdateSaleInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    sale = graphene.Field(SaleType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        try:
            sale = Sale.objects.get(id=input.sale_id)

            # Store original customer for credit recalculation
            original_customer = sale.customer

            if input.customer_id:
                try:
                    customer = Customer.objects.get(id=input.customer_id)
                    sale.customer = customer
                except Customer.DoesNotExist:
                    return UpdateSale(
                        success=False,
                        message="Customer not found",
                        errors=["Customer not found"],
                    )

            if input.discount is not None:
                sale.discount = input.discount

            # Recalculate total based on new discount
            sale.total = sale.subtotal - sale.discount

            # If customer changed or discount changed, recalculate credit automatically
            if sale.customer:
                # Calculate total payments already made
                total_payments = sum(
                    payment.amount for payment in sale.payments.all() if payment.amount
                )

                # Get customer's current credit balance
                current_customer_balance = sale.customer.get_current_credit_balance()

                # Calculate how much is owed after payments
                amount_owed_after_payments = sale.total - total_payments

                # Reset credit applied and recalculate
                credit_applied = Decimal("0.00")

                if amount_owed_after_payments > 0 and current_customer_balance > 0:
                    # Apply credit to cover shortfall
                    credit_applied = min(
                        current_customer_balance, amount_owed_after_payments
                    )

                sale.credit_applied = credit_applied
                sale.amount_due = Decimal(
                    max(0, sale.total - total_payments - credit_applied)
                )
                sale.balance = Decimal(sale.amount_due)
            else:
                # No customer, no credit applied
                total_payments = sum(
                    payment.amount for payment in sale.payments.all() if payment.amount
                )
                sale.credit_applied = Decimal("0.00")
                sale.amount_due = Decimal(max(0, sale.total - total_payments))
                sale.balance = Decimal(sale.amount_due)

            sale.save()

            return UpdateSale(
                success=True,
                message="Sale updated successfully with automatic credit recalculation",
                sale=sale,
            )

        except Sale.DoesNotExist:
            return UpdateSale(
                success=False, message="Sale not found", errors=["Sale not found"]
            )
        except Exception as e:
            return UpdateSale(
                success=False,
                message=f"Failed to update sale: {str(e)}",
                errors=[str(e)],
            )


class AddPayment(graphene.Mutation):
    """Add a payment to an existing sale"""

    class Arguments:
        input = AddPaymentInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    payment = graphene.Field(PaymentType)
    sale = graphene.Field(SaleType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        try:
            sale = Sale.objects.get(id=input.sale_id)

            # Create payment
            payment = Payment.objects.create(
                sale=sale,
                method=input.method,
                amount=input.amount,
                balance=input.balance,
            )

            # Update sale balance
            sale.balance = sale.balance - input.amount
            sale.amount_due = max(0, sale.amount_due - input.amount)
            sale.save()

            return AddPayment(
                success=True,
                message="Payment added successfully",
                payment=payment,
                sale=sale,
            )

        except Sale.DoesNotExist:
            return AddPayment(
                success=False, message="Sale not found", errors=["Sale not found"]
            )
        except Exception as e:
            return AddPayment(
                success=False,
                message=f"Failed to add payment: {str(e)}",
                errors=[str(e)],
            )


class AddCustomerCredit(graphene.Mutation):
    """Add credit to customer account"""

    class Arguments:
        input = CustomerCreditInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    credit = graphene.Field(CustomerCreditType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        try:
            customer = Customer.objects.get(id=input.customer_id)

            # Get current balance
            latest_credit = (
                CustomerCredit.objects.filter(customer=customer)
                .order_by("-created_at")
                .first()
            )

            current_balance = latest_credit.balance_after if latest_credit else 0

            # Calculate new balance
            if input.transaction_type == "credit_added":
                new_balance = current_balance + input.amount
            elif input.transaction_type == "credit_used":
                if current_balance < input.amount:
                    raise ValueError("Insufficient credit balance")
                new_balance = current_balance - input.amount
            elif input.transaction_type == "credit_refund":
                new_balance = current_balance + input.amount
            else:
                raise ValueError("Invalid transaction type")

            # Get sale if provided
            sale = None
            if input.sale_id:
                try:
                    sale = Sale.objects.get(id=input.sale_id)
                except Sale.DoesNotExist:
                    pass

            # Create credit transaction
            credit = CustomerCredit.objects.create(
                customer=customer,
                transaction_type=input.transaction_type,
                amount=input.amount,
                balance_after=new_balance,
                sale=sale,
                description=input.description or "",
            )

            return AddCustomerCredit(
                success=True,
                message="Credit transaction added successfully",
                credit=credit,
            )

        except Customer.DoesNotExist:
            return AddCustomerCredit(
                success=False,
                message="Customer not found",
                errors=["Customer not found"],
            )
        except Exception as e:
            return AddCustomerCredit(
                success=False,
                message=f"Failed to add credit: {str(e)}",
                errors=[str(e)],
            )


class CreateReturn(graphene.Mutation):
    """Create a new return request"""

    class Arguments:
        input = CreateReturnInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    return_request = graphene.Field(ReturnType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        try:
            # Get the original sale
            try:
                sale = Sale.objects.get(id=input.sale_id)
            except Sale.DoesNotExist:
                return CreateReturn(
                    success=False,
                    message="Sale not found",
                    errors=["Sale not found"],
                )

            # Get customer from sale
            customer = sale.customer
            if not customer:
                return CreateReturn(
                    success=False,
                    message="Cannot create return for sale without customer",
                    errors=["Sale must have a customer for returns"],
                )

            # Create the return request
            return_request = Return.objects.create(
                original_sale=sale,
                customer=customer,
                reason=input.reason,
            )

            # Add return items and calculate total refund
            total_refund = Decimal("0.00")
            for item_input in input.items:
                try:
                    sale_item = SaleItem.objects.get(
                        id=item_input.sale_item_id, sale=sale
                    )

                    # Validate quantity
                    if item_input.quantity > sale_item.quantity:
                        raise ValueError(
                            f"Return quantity ({item_input.quantity}) cannot exceed "
                            f"original quantity ({sale_item.quantity}) for {sale_item.product.name}"
                        )

                    # Create return item
                    return_item = ReturnItem.objects.create(
                        return_request=return_request,
                        original_sale_item=sale_item,
                        product=sale_item.product,
                        quantity=item_input.quantity,
                        unit_price=sale_item.unit_price,
                        refund_amount=item_input.refund_amount,
                    )

                    total_refund += item_input.refund_amount

                except SaleItem.DoesNotExist:
                    raise ValueError(f"Sale item not found: {item_input.sale_item_id}")

            # Update total refund amount
            return_request.total_refund_amount = total_refund
            return_request.save()

            return CreateReturn(
                success=True,
                message=f"Return request {return_request.return_id} created successfully",
                return_request=return_request,
            )

        except Exception as e:
            traceback.print_exc()
            return CreateReturn(
                success=False,
                message=f"Failed to create return: {str(e)}",
                errors=[str(e)],
            )


class ApproveReturn(graphene.Mutation):
    """Approve a return request and update stock"""

    class Arguments:
        input = ApproveReturnInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    return_request = graphene.Field(ReturnType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        try:
            # Get the return request
            try:
                return_request = Return.objects.get(id=input.return_id)
            except Return.DoesNotExist:
                return ApproveReturn(
                    success=False,
                    message="Return request not found",
                    errors=["Return request not found"],
                )

            # Get current user (you may need to adjust this based on your auth setup)
            user = info.context.user if hasattr(info.context, "user") else None
            if not user or not user.is_authenticated:
                return ApproveReturn(
                    success=False,
                    message="Authentication required",
                    errors=["Must be authenticated to approve returns"],
                )

            # Approve the return (this will update stock automatically)
            return_request.approve_return(
                approved_by_user=user, notes=input.approval_notes or ""
            )

            return ApproveReturn(
                success=True,
                message=f"Return {return_request.return_id} approved and completed successfully",
                return_request=return_request,
            )

        except ValueError as e:
            return ApproveReturn(
                success=False,
                message=str(e),
                errors=[str(e)],
            )
        except Exception as e:
            traceback.print_exc()
            return ApproveReturn(
                success=False,
                message=f"Failed to approve return: {str(e)}",
                errors=[str(e)],
            )


class RejectReturn(graphene.Mutation):
    """Reject a return request"""

    class Arguments:
        input = RejectReturnInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    return_request = graphene.Field(ReturnType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        try:
            # Get the return request
            try:
                return_request = Return.objects.get(id=input.return_id)
            except Return.DoesNotExist:
                return RejectReturn(
                    success=False,
                    message="Return request not found",
                    errors=["Return request not found"],
                )

            # Get current user
            user = info.context.user if hasattr(info.context, "user") else None
            if not user or not user.is_authenticated:
                return RejectReturn(
                    success=False,
                    message="Authentication required",
                    errors=["Must be authenticated to reject returns"],
                )

            # Reject the return
            return_request.reject_return(
                rejected_by_user=user, notes=input.rejection_notes
            )

            return RejectReturn(
                success=True,
                message=f"Return {return_request.return_id} rejected successfully",
                return_request=return_request,
            )

        except ValueError as e:
            return RejectReturn(
                success=False,
                message=str(e),
                errors=[str(e)],
            )
        except Exception as e:
            traceback.print_exc()
            return RejectReturn(
                success=False,
                message=f"Failed to reject return: {str(e)}",
                errors=[str(e)],
            )


class Mutation(graphene.ObjectType):
    """Sales mutations"""

    create_sale = CreateSale.Field()
    update_sale = UpdateSale.Field()
    add_payment = AddPayment.Field()
    add_customer_credit = AddCustomerCredit.Field()

    # Return mutations
    create_return = CreateReturn.Field()
    approve_return = ApproveReturn.Field()
    reject_return = RejectReturn.Field()
