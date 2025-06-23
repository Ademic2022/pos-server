import graphene


class StockDataInput(graphene.InputObjectType):
    """Input type for creating/updating StockData"""

    delivered_quantity = graphene.Float(required=True)
    price = graphene.Decimal(required=True)
    supplier = graphene.String(required=True)
    cumulative_stock = graphene.Float(required=True)
    remaining_stock = graphene.Float(required=True)
    sold_stock = graphene.Float(default_value=0.0)


class UpdateStockDataInput(graphene.InputObjectType):
    """Input type for updating existing StockData"""

    id = graphene.ID(required=True)
    delivered_quantity = graphene.Float()
    price = graphene.Decimal()
    supplier = graphene.String()
    cumulative_stock = graphene.Float()
    remaining_stock = graphene.Float()
    sold_stock = graphene.Float()


class RecordSaleInput(graphene.InputObjectType):
    """Input type for recording a sale"""

    stock_data_id = graphene.ID(required=True)
    quantity_sold = graphene.Float(required=True)
