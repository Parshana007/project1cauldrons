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


    with db.engine.begin() as connection:
        for potion in potions_delivered:
                connection.execute(sqlalchemy.text(
                    """
                    INSERT INTO barrel_ledger_entries (red_ml_delta,green_ml_delta, blue_ml_delta, dark_ml_delta)
                    VALUES (:red_ml, :green_ml, :blue_ml, :dark_ml)
                    """
                    ), 
                [{"red_ml": -potion.potion_type[0] * potion.quantity, "green_ml": -potion.potion_type[1] * potion.quantity, "blue_ml": -potion.potion_type[2] * potion.quantity, "dark_ml": -potion.potion_type[3] * potion.quantity}])

                connection.execute(sqlalchemy.text(
                    """
                    INSERT INTO potion_ledger_entries (potion_id, quantity_delta)
                    VALUES (
                        (SELECT potion_id FROM potion_catalog WHERE red_ml = :red_ml AND green_ml = :green_ml AND blue_ml = :blue_ml AND dark_ml = :dark_ml), :quantity)
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
            SELECT COALESCE(SUM(red_ml_delta),0) AS num_red_ml, 
                    COALESCE(SUM(green_ml_delta),0) AS num_green_ml, 
                    COALESCE(SUM(blue_ml_delta),0) AS num_blue_ml, 
                    COALESCE(SUM(dark_ml_delta),0) AS num_dark_ml
            FROM barrel_ledger_entries
            """)).first()
        quantity_potions_result = connection.execute(sqlalchemy.text(
            """
            SELECT sku, red_ml, green_ml, blue_ml, dark_ml, cost, COALESCE(SUM(potion_ledger_entries.quantity_delta), 0) AS quantity 
            FROM potion_ledger_entries
            RIGHT JOIN potion_catalog ON potion_ledger_entries.potion_id = potion_catalog.potion_id
            GROUP BY potion_catalog.potion_id
            """)).fetchall()

    num_red_ml = num_ml_data.num_red_ml
    num_green_ml = num_ml_data.num_green_ml
    num_blue_ml = num_ml_data.num_blue_ml
    num_dark_ml = num_ml_data.num_dark_ml

    potions_list = []

    print("get_bottle_plan: quantity_potions_result ", quantity_potions_result)
    total_quantity_sum = sum(item.quantity for item in quantity_potions_result)
    total_quantity_make = 0

    for potion in quantity_potions_result:
        if total_quantity_sum < 6 and potion.quantity < 2:
            print("get_bottle_plan: potion ",potion)
            while potion.red_ml <= num_red_ml and potion.green_ml <= num_green_ml and potion.blue_ml <= num_blue_ml and potion.dark_ml <= num_dark_ml and total_quantity_make < 6:

                num_red_ml -= potion.red_ml
                num_green_ml -= potion.green_ml
                num_blue_ml -= potion.blue_ml
                num_dark_ml -= potion.dark_ml

                print("get_bottle_plan: num_red_ml ", num_red_ml)
                print("get_bottle_plan: num_green_ml ", num_green_ml)
                print("get_bottle_plan: num_blue_ml ", num_blue_ml)
                print("get_bottle_plan: num_dark_ml ", num_dark_ml)

                total_quantity_make += 1
                print("total_quantity_make", total_quantity_make)

            if total_quantity_make != 0:
                potions_list.append({
                    "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
                    "quantity": total_quantity_make
                })
            total_quantity_sum += total_quantity_make
            total_quantity_make = 0

        print("get_bottle_plan: num_red_ml ", num_red_ml)
        print("get_bottle_plan: num_green_ml ", num_green_ml)
        print("get_bottle_plan: num_blue_ml ", num_blue_ml)
        print("get_bottle_plan: num_dark_ml ", num_dark_ml)
        print("get_bottle_plan: potions_list ", potions_list)

    return potions_list