from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

# * the total cost per barrel is the price to get how many barrels you want from one Barrel you
# * multiply the price of the barrel by the quanitity 
# * to get the ml you want to optimize by multiplying the ml_per_barrel by the quantity

class Barrel(BaseModel):
    sku: str # this can be SMALL_RED_BARREL, SMALL_GREEN_BARREL, SMALL_BLUE_BARREL, MEDIUM_RED_BARREL, MEDIUM_GREEN_BARREL, MEDIUM_BLUE_BARREL, LARGE_RED_BARREL, LARGE_GREEN_BARREL, LARGE_BLUE_BARREL

    ml_per_barrel: int
    potion_type: list[int] # if this is [100, 0, 0, 0] I know it's red if it's [0, 100, 0, 0] it's green
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]): #gives me a total num of barrels to be purchased
    """ """
    print("post_deliver_barrels:barrels_delivered ", barrels_delivered)

    gold_count = 0
    updated_red_ml, updated_green_ml, updated_blue_ml, updated_dark_ml  = 0, 0, 0, 0

    for barrel in barrels_delivered:
        gold_count += barrel.price * barrel.quantity
        if barrel.potion_type == [1, 0, 0, 0]: # RED
            updated_red_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 1, 0, 0]: # GREEN
            updated_green_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 1, 0]: # BLUE
            updated_blue_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 0, 1]: # DARK
            updated_dark_ml += barrel.ml_per_barrel * barrel.quantity
        else:
            raise Exception("Invalid potion type")
        
        print("post_deliver_barrels: gold_amount ", gold_count)
        print("post_deliver_barrels: red_ml ", updated_red_ml)
        print("post_deliver_barrels: green_ml ", updated_green_ml)
        print("post_deliver_barrels: blue_ml ", updated_blue_ml)
        print("post_deliver_barrels: dark_ml ", updated_dark_ml)

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO barrel_ledger_entries (red_ml_delta,green_ml_delta, blue_ml_delta, dark_ml_delta)
            VALUES (:updated_red_ml, :updated_green_ml, :updated_blue_ml, :updated_dark_ml)
            """
        ), [{"updated_red_ml": updated_red_ml, "updated_green_ml": updated_green_ml, "updated_blue_ml": updated_blue_ml, "updated_dark_ml": updated_dark_ml}])
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO gold_ledger_entries (gold_delta)
            VALUES (:gold_count)
            """
        ), [{"gold_count": -gold_count}])

    return "OK"


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("get_wholesale_purchase_plan: wholesale_catalog ", wholesale_catalog)

    #decision logic (like the conditional) should go into the plan, since that is where you do the planning
    #getting the num_red_potions
    with db.engine.begin() as connection:
        result_ml = connection.execute(sqlalchemy.text(
            """
            SELECT COALESCE(SUM(red_ml_delta),0) AS num_red_ml, 
                    COALESCE(SUM(green_ml_delta),0) AS num_green_ml, 
                    COALESCE(SUM(blue_ml_delta),0) AS num_blue_ml, 
                    COALESCE(SUM(dark_ml_delta),0) AS num_dark_ml
            FROM barrel_ledger_entries"""
            )).first()
        result_gold = connection.execute(sqlalchemy.text(
            """
            SELECT COALESCE(SUM(gold_delta),0) AS gold
            FROM gold_ledger_entries
            """
        )).first()
        
    gold_amount = result_gold.gold

    total_barrels, total_red_barrels, total_green_barrels, total_blue_barrels, total_dark_barrels = 0, 0, 0, 0, 0
    total_barrels_list = []
    print("gold_amount", gold_amount)

    barrel_conditions = [
        {"potion_type": [1, 0, 0, 0], "total_barrels_type": total_red_barrels, "ml_curr": result_ml.num_red_ml},
        {"potion_type": [0, 1, 0, 0], "total_barrels_type": total_green_barrels, "ml_curr": result_ml.num_green_ml},
        {"potion_type": [0, 0, 1, 0], "total_barrels_type": total_blue_barrels, "ml_curr": result_ml.num_blue_ml},
        {"potion_type": [0, 0, 0, 1], "total_barrels_type": total_dark_barrels, "ml_curr": result_ml.num_dark_ml}
    ]

    for barrel in wholesale_catalog:
        print("barrel ", barrel)
        quantity_to_purchase = int(gold_amount // barrel.price)

        print("get_wholesale_purchase_plan: quantity_to_purchase ", quantity_to_purchase)

        if quantity_to_purchase > 0 and barrel.potion_type != [1, 0, 0, 0]:
            for barrel_condition in barrel_conditions:
                if quantity_to_purchase > barrel.quantity: #to maximize the num of barrels are bought
                    quantity_to_purchase = barrel.quantity
                
                if barrel.potion_type == barrel_condition["potion_type"] and barrel_condition["total_barrels_type"] < 1 and barrel_condition["ml_curr"] < 100:
                    barrel_condition["total_barrels_type"] += quantity_to_purchase
                    total_barrels_list.append({
                        "sku": barrel.sku,
                        "quantity": quantity_to_purchase
                    })
                    gold_amount -= barrel.price * quantity_to_purchase
                    print("barrel_sku", barrel.sku)
                elif "BARREL" not in barrel.sku:
                    raise Exception("Invalid potion type")
            
            print("gold_amount ", gold_amount)
            print("total_barrels_list ", total_barrels_list)

    total_barrels = barrel_conditions[0]["total_barrels_type"] + barrel_conditions[1]["total_barrels_type"] + barrel_conditions[2]["total_barrels_type"] + barrel_conditions[3]["total_barrels_type"]

    print("get_wholesale_purchase_plan: total_barrels ", total_barrels)
    print("get_wholesale_purchase_plan: total_red_barrels ", barrel_conditions[0]["total_barrels_type"])
    print("get_wholesale_purchase_plan: total_green_barrels ", barrel_conditions[1]["total_barrels_type"])
    print("get_wholesale_purchase_plan: total_blue_barrels ", barrel_conditions[2]["total_barrels_type"])
    print("get_wholesale_purchase_plan: total_dark_barrels ", barrel_conditions[3]["total_barrels_type"])
    print("get_wholesale_purchase_plan: gold_amount ", gold_amount)

    print("get_wholesale_purchase_plan: total_barrels_list ", total_barrels_list)

    return total_barrels_list
