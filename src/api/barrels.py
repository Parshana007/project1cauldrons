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

    color_key = {
        "RED": "num_red_ml",
        "GREEN": "num_green_ml",
        "BLUE": "num_blue_ml"
    }
    #The deliver should be adding ml and subtracting gold. But should be based on how much gold and ml you already have
    #get total red_ml from Barrel
    for barrel in barrels_delivered:
        print("post_deliver_barrels: barrel.sku ", barrel.sku)
        if "RED" in barrel.sku:
            barrel_ml = barrel.ml_per_barrel * barrel.quantity
            gold_amount = barrel.price * barrel.quantity
            key = "RED"  
        elif "GREEN" in barrel.sku:
            barrel_ml = barrel.ml_per_barrel * barrel.quantity
            gold_amount = barrel.price * barrel.quantity
            key = "GREEN"
        elif "BLUE" in barrel.sku:
            barrel_ml = barrel.ml_per_barrel * barrel.quantity
            gold_amount = barrel.price * barrel.quantity
            key = "BLUE"
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {color_key[key]} = {color_key[key]} + {barrel_ml}"))
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {gold_amount}")) 
        print("post_deliver_barrels: gold_amount ", gold_amount)
        print("post_deliver_barrels: barrel_ml ", barrel_ml)
        print("post_deliver_barrels: barrel.potion_type", barrel.potion_type)

    return "OK"


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("get_wholesale_purchase_plan: wholesale_catalog ", wholesale_catalog)

    #decision logic (like the conditional) should go into the plan, since that is where you do the planning
    #getting the num_red_potions
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions, gold FROM global_inventory"))
        query = result.first()
    
    nums_red_potions = query.num_red_potions
    nums_green_potions = query.num_green_potions
    nums_blue_potions = query.num_blue_potions
    gold_amount = query.gold

    print("get_wholesale_purchase_plan: nums_red_potions ", nums_red_potions)
    print("get_wholesale_purchase_plan: nums_green_potions ", nums_green_potions)
    print("get_wholesale_purchase_plan: nums_blue_potions ", nums_blue_potions)
    print("get_wholesale_purchase_plan: gold_amount ", gold_amount)

    total_barrels = 0
    total_red_barrels = 0
    total_green_barrels = 0
    total_blue_barrels = 0
    quantity_to_purchase = 0

    for barrel in wholesale_catalog:
        quantity_to_purchase = gold_amount // barrel.price

        print("get_wholesale_purchase_plan: quantity_to_purchase ", quantity_to_purchase)

        if quantity_to_purchase > 0:
            if quantity_to_purchase > barrel.quantity:
                quantity_to_purchase = barrel.quantity

            if "RED" in barrel.sku and nums_red_potions < 10:
                total_red_barrels += quantity_to_purchase
                gold_amount -= barrel.price * quantity_to_purchase
            elif "GREEN" in barrel.sku and nums_green_potions < 10:
                total_green_barrels += quantity_to_purchase
                gold_amount -= barrel.price * quantity_to_purchase
            elif "BLUE" in barrel.sku and nums_blue_potions < 10:
                total_blue_barrels += quantity_to_purchase
                gold_amount -= barrel.price * quantity_to_purchase

    total_barrels = total_red_barrels + total_green_barrels + total_blue_barrels

    print("get_wholesale_purchase_plan: total_barrels ", total_barrels)
    print("get_wholesale_purchase_plan: total_red_barrels ", total_red_barrels)
    print("get_wholesale_purchase_plan: total_green_barrels ", total_green_barrels)
    print("get_wholesale_purchase_plan: total_blue_barrels ", total_blue_barrels)
    
    if total_barrels <= 0:
        return []
    
    total_barrels_list = []

    if total_red_barrels > 0:
        total_barrels_list.append({ 
                "sku": "SMALL_RED_BARREL",
                "quantity": total_red_barrels,
        })
    if total_green_barrels > 0:
        total_barrels_list.append({ 
                "sku": "SMALL_GREEN_BARREL",
                "quantity": total_green_barrels,
        })
    if total_blue_barrels > 0:
        total_barrels_list.append({ 
                "sku": "SMALL_BLUE_BARREL",
                "quantity": total_blue_barrels,
        })

    print("get_wholesale_purchase_plan: total_barrels_list ", total_barrels_list)

    return total_barrels_list
