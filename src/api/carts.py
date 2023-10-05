from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class Customer:
    def __init__(self, name, potions_bought, gold_paid):
        self.name = name
        self.potions_bought = potions_bought
        self.gold_paid = gold_paid

cart_id_counter = 0

my_dict = {} 

class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    global cart_id_counter
    cart_id_counter += 1
    my_dict[cart_id_counter] = Customer(new_cart.customer, [0, 0, 0, 0], 0)
    return {"cart_id" : cart_id_counter} 

@router.get("/{cart_id}")
def get_cart(cart_id: int): 
    """ """
    if cart_id in my_dict:
        return my_dict[cart_id] # return whole customer object
    else:
        return {} #cart_id doesn't exist


class CartItem(BaseModel):
    quantity: int #? Does this just tell me total num of potions? How to separate by type?


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem): 
    """ """
    color_key = {
        "RED": 0,
        "GREEN": 1,
        "BLUE": 2
    }
    # my_dict[cart_id].potions_bought[0] = cart_item.quantity
    if "RED" in item_sku: 
        key = "RED"
    elif "GREEN" in item_sku:
        key = "GREEN"
    elif "BLUE" in item_sku:
        key = "BLUE"

    my_dict[cart_id].gold_paid = cart_item.quantity * 100
    my_dict[cart_id].potions_bought[color_key[key]] += cart_item.quantity  # each potion = 100 gold

    return "OK"


class CartCheckout(BaseModel):
    payment: str #? What is this supposed to be?

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout): 
    """ """
    total_red_potions = my_dict[cart_id].potions_bought[0]
    total_green_potions = my_dict[cart_id].potions_bought[1]
    total_blue_potions = my_dict[cart_id].potions_bought[2]

    total_potions_bought = total_red_potions + total_green_potions + total_blue_potions

    # with db.engine.begin() as connection:
    #     result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory"))
    #     potions_row = result.first()

    # nums_red_potions = potions_row.num_red_potions
    # nums_green_potions = potions_row.num_green_potions
    # nums_blue_potions = potions_row.num_blue_potions

    # if total_potions_bought > nums_red_potions: #? Do I need to check if customer can buy?
    #     total_potions_bought = nums_red_potions

    total_gold_paid = total_potions_bought * 100
    my_dict[cart_id].gold_paid = my_dict[cart_id].gold_paid

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = num_red_potions - {total_red_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions - {total_green_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = num_blue_potions - {total_blue_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold + {total_gold_paid}"))

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
