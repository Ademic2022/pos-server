import graphene


class UpdateStockDeliveryInput(graphene.InputObjectType):
    """Input type for updating existing StockData"""

    id = graphene.ID(required=True)
    delivered_quantity = graphene.Float()
    price = graphene.Decimal()
    supplier = graphene.String()
    sold_stock = graphene.Float()


class RecordSaleInput(graphene.InputObjectType):
    """Input type for recording a sale"""

    stock_data_id = graphene.ID(required=True)
    quantity_sold = graphene.Float(required=True)
