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
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory"))

        potion_data = result.first()
    
    nums_red_potions = potion_data.num_red_potions
    nums_green_potions = potion_data.num_green_potions
    nums_blue_potions = potion_data.num_blue_potions

    total_potions = nums_red_potions + nums_green_potions + nums_blue_potions

    if total_potions == 0:
        return []
    
    potion_list = []

    if nums_red_potions != 0:
        potion_list.append({ 
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": nums_red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
        })
    if nums_green_potions != 0:
        potion_list.append({ 
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": nums_green_potions,
                "price": 50,
                "potion_type": [0, 100, 0, 0], 
        })
    if nums_blue_potions != 0:
        potion_list.append({ 
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": nums_blue_potions,
                "price": 50,
                "potion_type": [0, 0, 100, 0],
        })


    return potion_list
