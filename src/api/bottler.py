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
    print("post_deliver_bottles: potions_delivered", potions_delivered)


    for potion in potions_delivered:
        with db.engine.begin() as connection:
            connection.execute(
                sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                num_red_ml = num_red_ml - :red_ml,
                num_green_ml = num_green_ml - :green_ml,
                num_blue_ml = num_blue_ml - :blue_ml,
                num_dark_ml = num_dark_ml - :dark_ml
                """
                ),
            [{"red_ml": potion.potion_type[0], "green_ml": potion.potion_type[1], "blue_ml": potion.potion_type[2], "dark_ml": potion.potion_type[3]}])

            connection.execute( #based on the matching red_ml, green_ml, blue_ml, dark_ml updated that quantity
                sqlalchemy.text(
                """
                UPDATE potion_catalog SET
                quantity = quantity + :quantity
                WHERE red_ml = :red_ml AND green_ml = :green_ml AND blue_ml = :blue_ml AND dark_ml = :dark_ml
                """
                ),
            [{"quantity": potion.quantity, "red_ml": potion.potion_type[0], "green_ml": potion.potion_type[1], "blue_ml": potion.potion_type[2], "dark_ml": potion.potion_type[3]}])
            
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
        num_ml_data = connection.execute(sqlalchemy.text(
            """
            SELECT SUM(red_ml_delta) AS num_red_ml, 
                    SUM(green_ml_delta) AS num_green_ml, 
                    SUM(blue_ml_delta) AS num_blue_ml, 
                    SUM(dark_ml_delta) AS num_dark_ml
            FROM barrel_ledger_entries
            """)).first()
        quantity_potions_result = connection.execute(sqlalchemy.text(
            """
            SELECT sku, red_ml, green_ml, blue_ml, dark_ml, cost, SUM(potion_ledger_entries.quantity_delta) AS quantity 
            FROM potion_ledger_entries
            RIGHT JOIN potion_catalog ON potion_ledger_entries.potion_id = potion_catalog.potion_id
            GROUP BY potion_catalog.potion_id
            HAVING SUM(potion_ledger_entries.quantity_delta) is NULL
            """)).fetchall()

    num_red_ml = num_ml_data.num_red_ml
    num_green_ml = num_ml_data.num_green_ml
    num_blue_ml = num_ml_data.num_blue_ml
    num_dark_ml = num_ml_data.num_dark_ml

    potions_list = []

    print("get_bottle_plan: quantity_potions_result ", quantity_potions_result)

    for potion in quantity_potions_result:
        print("get_bottle_plan: potion ",potion)
        if potion.red_ml <= num_red_ml and potion.green_ml <= num_green_ml and potion.blue_ml <= num_blue_ml and potion.dark_ml <= num_dark_ml:

            potions_list.append({
                "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
                "quantity": 1
            })

            num_red_ml -= potion.red_ml
            num_green_ml -= potion.green_ml
            num_blue_ml -= potion.blue_ml
            num_dark_ml -= potion.dark_ml

    print("get_bottle_plan: num_red_ml ", num_red_ml)
    print("get_bottle_plan: num_green_ml ", num_green_ml)
    print("get_bottle_plan: num_blue_ml ", num_blue_ml)
    print("get_bottle_plan: num_dark_ml ", num_dark_ml)
    print("get_bottle_plan: potions_list ", potions_list)

    return potions_list