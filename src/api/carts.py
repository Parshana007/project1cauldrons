from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class NewCart(BaseModel):
    customer: str
 

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO carts (customer_name)
                VALUES (:customer_name)
                RETURNING cart_id"""
        ), [{"customer_name" : new_cart.customer}]).scalar()

    print("create_cart: result ", result)
    return {"cart_id" : result} 

@router.get("/{cart_id}")
def get_cart(cart_id: int): 
    """ """ #TODO make a join to get the quantity total of a cart
    # with db.engine.begin() as connection:
    #     result = connection.execute(
    #         sqlalchemy.text(
    #         """
    #         SELECT * 
    #         FROM carts 
    #         WHERE cart_id = :cart_id
    #         """
    # ), [{"cart_id": cart_id}]).first() #Join on cart_items to get the total quantity of the cart

    quantity_to_buy = 0
    # SUM(cart_items.count_to_buy) AS quantity_to_buy
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(
            """
            SELECT carts.cart_id, customer_name, SUM(cart_items.count_to_buy) AS quantity_to_buy
            FROM carts 
            JOIN cart_items ON carts.cart_id = cart_items.cart_id
            WHERE carts.cart_id = :cart_id
            GROUP BY carts.cart_id, carts.customer_name
            """
    ), [{"cart_id": cart_id}]).first()
        
    print(result) # gives back (14, "Sammy", 3)
        
        
    if result is not None:
        return {
            "cart_id": cart_id,
            "customer_name": result.customer_name,
            "quantity_to_buy": result.quantity_to_buy
        }
    return {}


class CartItem(BaseModel):
    quantity: int 


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem): 
    """ """
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO cart_items (cart_id, sku, count_to_buy)
                VALUES (:cart_id, :sku, :count_to_buy)
                """
        ), [{"cart_id" : cart_id, "sku": item_sku, "count_to_buy": cart_item.quantity}])

    print("set_item_quantity: cart_id ", cart_id)
    print("set_item_quantity: item_sku ", item_sku)
    print("set_item_quantity: cart_item.quantity ", cart_item.quantity)

    return "OK"


class CartCheckout(BaseModel):
    payment: str #? What is this supposed to be?

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout): 
    """ """
    # find the potion that matches the cart_id
    # grab all info of the specific item in cart_items all instance where cart_id is the checkout id
    # update the potion_catalog to correctly subtract the quantity of the potion
    # update global_inventory for the gold 
    total_potions_bought = 0
    total_gold_paid = 0
    
    with db.engine.begin() as connection:
        cart_info = connection.execute(
            sqlalchemy.text(
                """
                SELECT cart_id, sku, count_to_buy
                FROM cart_items
                WHERE cart_id = :cart_id
                """
        ), [{"cart_id": cart_id}]).fetchall()

    print("checkout: cart_info ", cart_info)

    for cart_to_buy in cart_info:
        print("checkout: cart_to_buy ", cart_to_buy)
        with db.engine.begin() as connection:
            potion_info = connection.execute(
                sqlalchemy.text( #TODO try to optimize this query into one [make join]
                    """
                    SELECT quantity, cost, sku 
                    FROM potion_catalog
                    WHERE potion_catalog.sku = :sku
                    """
            ), [{"sku": cart_to_buy.sku}]).first()
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE potion_catalog
                    SET quantity = quantity - :count_to_buy
                    WHERE potion_catalog.sku = :sku
                    """
            ), [{"count_to_buy": cart_to_buy.count_to_buy, "sku": cart_to_buy.sku}])
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE global_inventory
                    SET gold = gold + :customer_payed
                    """
            ), [{"customer_payed": cart_to_buy.count_to_buy * potion_info.cost}])

        total_potions_bought += cart_to_buy.count_to_buy
        total_gold_paid += cart_to_buy.count_to_buy * potion_info.cost
        print("checkout: total_potions_bought ", total_potions_bought)
        print("checkout: total_gold_paid ", total_gold_paid)

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
