from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

# * this catalog is our own for each potion therefore has our own sku 
# * while the barrels are from a wholesaler with their own sku

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    # query database for num of red potions in DB
    potion_list = []

    with db.engine.begin() as connection:
        # get all of the potions that are not 0
        result = connection.execute(sqlalchemy.text("SELECT * FROM potion_catalog WHERE quantity != 0"))

        potion_inventory_data = result.fetchall()

    for potion in potion_inventory_data:
        potion_list.append({
            "sku": potion.sku,
            "name": potion.sku,
            "quantity": potion.quantity,
            "price": potion.cost,
            "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
        })

    return potion_list
