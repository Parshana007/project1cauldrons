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
        self.potions_bought = potions_bought # ? Do I want this to be an array for diff kinds of potions
        self.gold_paid = gold_paid

cart_id_counter = 0

my_dict = {} # ? key is cart_id, value is Customer object, should this change

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
def get_cart(cart_id: int): # ? what does this function return?
    """ """
    if cart_id in my_dict:
        return my_dict[cart_id] # return whole customer object
    else:
        return {} #cart_id doesn't exist


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    my_dict[cart_id].potions_bought[0] = cart_item.quantity
    my_dict[cart_id].gold_paid = cart_item.quantity * 100
    # if str_cart_id in my_dict:
    #     if item_sku == "RED_POTION_0": 
    #         my_dict[str_cart_id].potions_bought[0] += cart_item.quantity # ? Update only the red potions 
    #         my_dict[str_cart_id].gold_paid += 100 # each potion = 100 gold

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout): # ? What is cart_checkout?
    """ """
    total_potions_bought = 0

    for potion in my_dict[cart_id].potions_bought:
        total_potions_bought += potion

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))

        red_potions = result.first()
        nums_red_potions = red_potions.num_red_potions

    if total_potions_bought > nums_red_potions:
        total_potions_bought = nums_red_potions
        
    total_gold_paid = total_potions_bought * 100
    my_dict[cart_id].gold_paid = my_dict[cart_id].gold_paid

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = num_red_potions - {total_potions_bought}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold + {total_gold_paid}"))

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
