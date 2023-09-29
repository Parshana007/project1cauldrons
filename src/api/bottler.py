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

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))

        num_red_ml_row = result.first()
        num_red_ml_total = num_red_ml_row.num_red_ml

    total_red_potions = num_red_ml_total // 100

    num_red_ml_total -= total_red_potions * 100

    # total_red_potions potion_delivered[0].quantity
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml_total"))

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = total_red_potions"))
    

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

    # Initial logic: bottle all barrels into red potions.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))

        num_red_ml_row = result.first()
        num_red_ml_total = num_red_ml_row.num_red_ml

    total_red_potions = num_red_ml_total // 100

    if total_red_potions == 0:
        return [] #not enough ml to make a potion

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": total_red_potions,
            }
        ]
