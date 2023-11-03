from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    potion_list = []

    with db.engine.begin() as connection:
        # get all of the potions that are not 0

        # SUM gives me sum of each unique instance of a potion_id as quantity without sum I would get repeated values in result table
        # must use group by to reflect the unique identifiers for the SUM aggregate function
        # join is necessary to connect a sku from one table with quantity from another table
        result = connection.execute(sqlalchemy.text(
            """
            SELECT sku, red_ml, green_ml, blue_ml, dark_ml, cost, COALESCE(SUM(potion_ledger_entries.quantity_delta), 0) AS quantity 
            FROM potion_ledger_entries
            INNER JOIN potion_catalog ON potion_ledger_entries.potion_id = potion_catalog.potion_id
            GROUP BY potion_catalog.potion_id
            """))

        potion_inventory_data = result.fetchall()
    potion_total_displayed = 0

    for potion in potion_inventory_data:
        potion_quantity = potion.quantity
        # print("potion_total_displayed", potion_total_displayed)

        if potion_quantity != 0 and potion_total_displayed < 6:
            potion_total_displayed += potion_quantity
            potion_list.append({
                "sku": potion.sku,
                "name": potion.sku,
                "quantity": potion_quantity, 
                "price": potion.cost,
                "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
            })

    return potion_list
