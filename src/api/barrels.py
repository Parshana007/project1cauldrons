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
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0

    for barrel in barrels_delivered:
        gold_count += barrel.price * barrel.quantity
        if barrel.potion_type == [1, 0, 0, 0]: # RED
            red_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 1, 0, 0]: # GREEN
            green_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 1, 0]: # BLUE
            blue_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 0, 1]: # DARK
            dark_ml += barrel.ml_per_barrel * barrel.quantity
        else:
            raise Exception("Invalid potion type")

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                red_ml = red_ml + :red_ml 
                green_ml = green_ml + :green_ml
                blue_ml = blue_ml + :blue_ml
                dark_ml = dark_ml + :dark_ml
                gold = gold - :gold_count
                """
                ),
            [{"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml, "gold_count": gold_count}])


        print("post_deliver_barrels: gold_amount ", gold_count)
        print("post_deliver_barrels: red_ml ", red_ml)
        print("post_deliver_barrels: green_ml ", green_ml)
        print("post_deliver_barrels: blue_ml ", blue_ml)
        print("post_deliver_barrels: dark_ml ", dark_ml)
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
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold FROM global_inventory"))
        query = result.first()
    
    num_red_ml = query.num_red_ml
    num_green_ml = query.num_green_ml
    num_blue_ml = query.num_blue_ml
    num_dark_ml = query.num_dark_ml
    gold_amount = query.gold

    print("get_wholesale_purchase_plan: num_red_ml ", num_red_ml)
    print("get_wholesale_purchase_plan: num_green_ml ", num_green_ml)
    print("get_wholesale_purchase_plan: num_blue_ml ", num_blue_ml)
    print("get_wholesale_purchase_plan: num_dark_ml ", num_dark_ml)
    print("get_wholesale_purchase_plan: gold_amount ", gold_amount)

    total_barrels = 0
    total_red_barrels = 0
    total_green_barrels = 0
    total_blue_barrels = 0
    total_dark_barrels = 0
    quantity_to_purchase = 0

    for barrel in wholesale_catalog:
        quantity_to_purchase = gold_amount // barrel.price

        print("get_wholesale_purchase_plan: quantity_to_purchase ", quantity_to_purchase)

        if quantity_to_purchase > 0:
            if barrel.potion_type == [1, 0, 0, 0] and total_red_barrels < 2:
                total_red_barrels += 1  
            elif barrel.potion_type == [0, 1, 0, 0] and total_green_barrels < 2:
                total_green_barrels += 1 
            elif barrel.potion_type == [0, 0, 1, 0] and total_blue_barrels < 2:
                total_blue_barrels += 1 
            elif barrel.potion_type == [0, 0, 0, 1] and total_dark_barrels < 2:
                total_dark_barrels += 1
            else:
                raise Exception("Invalid potion type")
            gold_amount -= barrel.price 

    total_barrels = total_red_barrels + total_green_barrels + total_blue_barrels + total_dark_barrels

    print("get_wholesale_purchase_plan: total_barrels ", total_barrels)
    print("get_wholesale_purchase_plan: total_red_barrels ", total_red_barrels)
    print("get_wholesale_purchase_plan: total_green_barrels ", total_green_barrels)
    print("get_wholesale_purchase_plan: total_blue_barrels ", total_blue_barrels)
    print("get_wholesale_purchase_plan: total_dark_barrels ", total_dark_barrels)
    print("get_wholesale_purchase_plan: gold_amount ", gold_amount)
    
    if total_barrels <= 0:
        return []
    
    total_barrels_list = []

    barrel_colors = ["RED_BARREL", "GREEN_BARREL", "BLUE_BARREL"]
    barrel_quantity = [total_red_barrels, total_green_barrels, total_blue_barrels, total_dark_barrels]

    for i in range(len(barrel_colors)):
        if barrel_quantity[i] > 0:
            total_barrels_list.append({
                "sku": barrel_colors[i],
                "quantity": barrel_quantity[i],
            })

    print("get_wholesale_purchase_plan: total_barrels_list ", total_barrels_list)

    return total_barrels_list
