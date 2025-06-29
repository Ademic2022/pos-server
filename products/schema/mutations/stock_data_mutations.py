import graphene
from products.models import StockData
from products.schema.types.stock_data_type import StockDataType
from products.schema.inputs.stock_data_inputs import (
    UpdateStockDeliveryInput,
    RecordSaleInput,
)


class AddStockDelivery(graphene.Mutation):
    """Create a new stock delivery using the rolling stock system"""

    class Arguments:
        delivered_quantity = graphene.Float(required=True)
        price = graphene.Decimal(required=True)
        supplier = graphene.String(required=True)

    stock_data = graphene.Field(StockDataType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, **kwargs):
        delivered_quantity = kwargs.get("delivered_quantity")
        price = kwargs.get("price")
        supplier = kwargs.get("supplier")

        try:
            stock_data = StockData.create_new_delivery(
                delivered_quantity=delivered_quantity,
                price=price,
                supplier=supplier,
            )
            stock_data.full_clean()
            stock_data.save()

            return AddStockDelivery(
                stock_data=stock_data,
                success=True,
                message=f"Stock delivery created: {delivered_quantity}L from {supplier}",
            )
        except Exception as e:
            return AddStockDelivery(stock_data=None, success=False, message=str(e))


class UpdateStockDelivery(graphene.Mutation):
    """Update existing stock data"""

    class Arguments:
        input = UpdateStockDeliveryInput(required=True)

    stock_data = graphene.Field(StockDataType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input):
        try:
            stock_data = StockData.objects.get(pk=input.id)

            # Update fields if provided
            if input.delivered_quantity is not None:
                stock_data.delivered_quantity = input.delivered_quantity
            if input.price is not None:
                stock_data.price = input.price
            if input.supplier is not None:
                stock_data.supplier = input.supplier
            if input.sold_stock is not None:
                stock_data.sold_stock = input.sold_stock

            stock_data.full_clean()
            stock_data.save()

            return UpdateStockDelivery(
                stock_data=stock_data,
                success=True,
                message="Stock data updated successfully",
            )
        except StockData.DoesNotExist:
            return UpdateStockDelivery(
                stock_data=None, success=False, message="Stock data not found"
            )
        except Exception as e:
            return UpdateStockDelivery(stock_data=None, success=False, message=str(e))


class RecordSale(graphene.Mutation):
    """Record a sale and update stock levels"""

    class Arguments:
        input = RecordSaleInput(required=True)

    stock_data = graphene.Field(StockDataType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input):
        try:
            stock_data = StockData.objects.get(pk=input.stock_data_id)

            # Record the sale
            stock_data.record_sale(input.quantity_sold)
            stock_data.save()

            return RecordSale(
                stock_data=stock_data,
                success=True,
                message=f"Sale recorded: {input.quantity_sold}L sold",
            )
        except StockData.DoesNotExist:
            return RecordSale(
                stock_data=None, success=False, message="Stock data not found"
            )
        except ValueError as e:
            return RecordSale(stock_data=None, success=False, message=str(e))
        except Exception as e:
            return RecordSale(stock_data=None, success=False, message=str(e))


class DeleteStockData(graphene.Mutation):
    """Delete stock data record"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id):
        try:
            stock_data = StockData.objects.get(pk=id)
            supplier = stock_data.supplier
            delivered_quantity = stock_data.delivered_quantity
            stock_data.delete()

            return DeleteStockData(
                success=True,
                message=f"Deleted stock delivery: {delivered_quantity}L from {supplier}",
            )
        except StockData.DoesNotExist:
            return DeleteStockData(success=False, message="Stock data not found")
        except Exception as e:
            return DeleteStockData(success=False, message=str(e))


class Mutation(graphene.ObjectType):
    """All StockData mutations"""

    # create_stock = CreateStock.Field()
    add_stock_delivery = AddStockDelivery.Field()
    update_stock_delivery = UpdateStockDelivery.Field()
    record_sale = RecordSale.Field()
    delete_stock_data = DeleteStockData.Field()
