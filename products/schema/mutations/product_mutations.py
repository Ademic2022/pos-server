import graphene
from products.models import Product
from products.schema.types.product_type import ProductType
from products.schema.inputs.product_inputs import ProductInput, UpdateProductInput
from decimal import Decimal


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        try:
            # Check if product with this ID already exists
            if Product.objects.filter(id=input.id).exists():
                return CreateProduct(
                    success=False,
                    errors=[f"Product with ID '{input.id}' already exists"],
                    product=None,
                )

            # Create the product
            product = Product.objects.create(
                id=input.id,
                name=input.name,
                price=Decimal(str(input.price)),  # Ensure price is a Decimal
                unit=input.unit,
                sale_type=input.sale_type.value,  # Convert enum to string value
            )

            return CreateProduct(success=True, errors=[], product=product)
        except Exception as e:
            return CreateProduct(success=False, errors=[str(e)], product=None)


class UpdateProduct(graphene.Mutation):
    class Arguments:
        id = graphene.String(required=True)
        input = UpdateProductInput(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    product = graphene.Field(ProductType)

    def mutate(self, info, id, input):
        try:
            product = Product.objects.get(id=id)

            # Update fields if provided
            if input.name is not None:
                product.name = input.name
            if input.price is not None:
                product.price = input.price
            if input.unit is not None:
                product.unit = input.unit
            if input.sale_type is not None:
                product.sale_type = input.sale_type

            product.save()

            return UpdateProduct(success=True, errors=[], product=product)
        except Product.DoesNotExist:
            return UpdateProduct(
                success=False,
                errors=[f"Product with ID '{id}' not found"],
                product=None,
            )
        except Exception as e:
            return UpdateProduct(success=False, errors=[str(e)], product=None)


class DeleteProduct(graphene.Mutation):
    class Arguments:
        id = graphene.String(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        try:
            product = Product.objects.get(id=id)
            product.delete()

            return DeleteProduct(success=True, errors=[])
        except Product.DoesNotExist:
            return DeleteProduct(
                success=False, errors=[f"Product with ID '{id}' not found"]
            )
        except Exception as e:
            return DeleteProduct(success=False, errors=[str(e)])


class Mutation(graphene.ObjectType):
    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()
