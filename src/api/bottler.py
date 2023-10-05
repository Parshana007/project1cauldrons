from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)

    color_key = {
        "num_red_potions": "num_red_ml",
        "num_green_potions": "num_green_ml",
        "num_blue_potions": "num_blue_ml"
    }

    for potions in potions_delivered:
        if potions.potion_type[0] != 0:
            total_potions = potions.quantity
            num_ml_total = total_potions * 100
            key = "num_red_potions"
            # print(total_red_potions)
            # print(num_red_ml_total)
        elif potions.potion_type[1] != 0:
            total_potions = potions.quantity
            num_ml_total = total_potions * 100
            key = "num_green_potions"
            # print(total_green_potions)
            # print(num_green_ml_total)
        elif potions.potion_type[2] != 0:
            total_potions = potions.quantity
            num_ml_total = total_potions * 100
            key = "num_blue_potions"
            # print(total_blue_potions)
            # print(num_blue_ml_total)
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {color_key[key]} = {color_key[key]} - {num_ml_total}"))
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {key} = {key} + {total_potions}"))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory"))

        num_ml_data = result.first()
    
    total_red_potions = num_ml_data.num_red_ml // 100
    total_green_potions = num_ml_data.num_green_ml // 100
    total_blue_potions = num_ml_data.num_blue_ml // 100

    total_potions = total_red_potions + total_green_potions + total_blue_potions

    if total_potions == 0:
        return [] #not enough ml to make a potion
    
    potions_list = []

    if total_red_potions > 0:
        potions_list.append({ 
                "potion_type": [100, 0, 0, 0],
                "quantity": total_red_potions,
        })
    if total_green_potions > 0:
        potions_list.append({ 
                "potion_type": [0, 100, 0, 0],
                "quantity": total_green_potions,
        })
    if total_blue_potions > 0:
        potions_list.append({ 
                "potion_type": [0, 0, 100, 0],
                "quantity": total_blue_potions,
        })

    return potions_list
