from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str 

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]): #gives me a total num of barrels to be purchased
    """ """
    print(barrels_delivered)

    #The deliver should be adding ml and subtracting gold. But should be based on how much gold and ml you already have

    #get total red_ml from Barrel
    for Barrel in barrels_delivered:
        barrel_red_ml = Barrel.ml_per_barrel
        gold_amount = Barrel.price
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml + {barrel_red_ml}"))

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {gold_amount}"))
    

    return "OK"


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    #decision logic (like the conditional) should go into the plan, since that is where you do the planning
    #getting the num_red_potions
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))

        red_potions_row = result.first()
        nums_red_potions = red_potions_row.num_red_potions

    #getting the gold total    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))

        gold_row = result.first()
        gold_amount = gold_row.gold
    
    total_barrels = 0

    if nums_red_potions < 10:
        for Barrel in wholesale_catalog:
            if Barrel.sku == "SMALL_RED_BARREL" and gold_amount >= Barrel.price:
                total_barrels += 1
                gold_amount -= Barrel.price

    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": total_barrels,
        }
    ]
