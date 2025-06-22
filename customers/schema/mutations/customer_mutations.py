import graphene
from django.db import transaction
from graphql_jwt.decorators import login_required
from customers.models import Customer
from customers.schema.types.customer_type import CustomerType
from customers.schema.inputs.customer_inputs import (
    CreateCustomerInput,
    UpdateCustomerInput,
)


class CreateCustomerMutation(graphene.Mutation):
    """Mutation to create a new customer"""

    class Arguments:
        input = CreateCustomerInput(required=True)

    success = graphene.Boolean()
    customer = graphene.Field(CustomerType)
    errors = graphene.List(graphene.String)

    @login_required
    def mutate(self, info, input):
        try:
            with transaction.atomic():
                # Check if phone already exists
                if Customer.objects.filter(phone=input.phone).exists():
                    return CreateCustomerMutation(
                        success=False,
                        errors=["A customer with this phone number already exists"],
                    )

                # Check if email already exists (if provided)
                if input.email and Customer.objects.filter(email=input.email).exists():
                    return CreateCustomerMutation(
                        success=False,
                        errors=["A customer with this email already exists"],
                    )

                # Create the customer
                customer = Customer.objects.create(
                    name=input.name,
                    email=input.email,
                    phone=input.phone,
                    address=input.address,
                    type=input.type.value,
                    credit_limit=input.credit_limit or 0,
                    notes=input.notes,
                    created_by=info.context.user,
                )

                return CreateCustomerMutation(success=True, customer=customer)

        except Exception as e:
            return CreateCustomerMutation(success=False, errors=[str(e)])


class UpdateCustomerMutation(graphene.Mutation):
    """Mutation to update an existing customer"""

    class Arguments:
        input = UpdateCustomerInput(required=True)

    success = graphene.Boolean()
    customer = graphene.Field(CustomerType)
    errors = graphene.List(graphene.String)

    @login_required
    def mutate(self, info, input):
        try:
            with transaction.atomic():
                # Get the customer
                try:
                    customer = Customer.objects.get(id=input.id)
                except Customer.DoesNotExist:
                    return UpdateCustomerMutation(
                        success=False, errors=["Customer not found"]
                    )

                # Check if phone already exists (if changing phone)
                if input.phone and input.phone != customer.phone:
                    if (
                        Customer.objects.filter(phone=input.phone)
                        .exclude(id=input.id)
                        .exists()
                    ):
                        return UpdateCustomerMutation(
                            success=False,
                            errors=["A customer with this phone number already exists"],
                        )

                # Check if email already exists (if changing email)
                if input.email and input.email != customer.email:
                    if (
                        Customer.objects.filter(email=input.email)
                        .exclude(id=input.id)
                        .exists()
                    ):
                        return UpdateCustomerMutation(
                            success=False,
                            errors=["A customer with this email already exists"],
                        )

                # Update the customer
                update_fields = []

                if input.name is not None:
                    customer.name = input.name
                    update_fields.append("name")

                if input.email is not None:
                    customer.email = input.email
                    update_fields.append("email")

                if input.phone is not None:
                    customer.phone = input.phone
                    update_fields.append("phone")

                if input.address is not None:
                    customer.address = input.address
                    update_fields.append("address")

                if input.type is not None:
                    customer.type = input.type.value
                    update_fields.append("type")

                if input.status is not None:
                    customer.status = input.status.value
                    update_fields.append("status")

                if input.credit_limit is not None:
                    customer.credit_limit = input.credit_limit
                    update_fields.append("credit_limit")

                if input.notes is not None:
                    customer.notes = input.notes
                    update_fields.append("notes")

                if update_fields:
                    update_fields.append("updated_at")
                    customer.save(update_fields=update_fields)

                return UpdateCustomerMutation(success=True, customer=customer)

        except Exception as e:
            return UpdateCustomerMutation(success=False, errors=[str(e)])


class DeleteCustomerMutation(graphene.Mutation):
    """Mutation to delete a customer"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @login_required
    def mutate(self, info, id):
        try:
            with transaction.atomic():
                try:
                    customer = Customer.objects.get(id=id)
                except Customer.DoesNotExist:
                    return DeleteCustomerMutation(
                        success=False, errors=["Customer not found"]
                    )

                # Check if customer has outstanding balance
                if customer.balance > 0:
                    return DeleteCustomerMutation(
                        success=False,
                        errors=["Cannot delete customer with outstanding balance"],
                    )

                customer.delete()

                return DeleteCustomerMutation(success=True)

        except Exception as e:
            return DeleteCustomerMutation(success=False, errors=[str(e)])


class Mutation(graphene.ObjectType):
    """Customer mutations"""

    create_customer = CreateCustomerMutation.Field()
    update_customer = UpdateCustomerMutation.Field()
    delete_customer = DeleteCustomerMutation.Field()
