from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from enum import Enum


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    
    line_items_query = cart_line_items_query()
    line_items = cart_line_items(line_items_query)
    filter_line_items = filtering(line_items, customer_name, potion_sku)
    sorted_line_items = sorting_col(filter_line_items, sort_col, sort_order)
    # prev_page_token, next_page_token, final_line_items = pagination_cart_items(sorted_line_items)

    # return {
    #     "prev_page_token" : prev_page_token,
    #     "next_page_token" : next_page_token,
    #     "result" : final_line_items,
    # }
    final_result_items = []

    for item in sorted_line_items:
        item_combined_sku = str(item.count_bought) + item.item_sku
        final_result_items.append(
            {"line_id": item.line_id, "customer_name": item.customer_name, "item_sku": item_combined_sku, "line_item_total": item.line_item_total, "timestamp": item.timestamp}
        )

    return {
        "previous": "",
        "next": "",
        "results": final_result_items
    }

    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.

    """
def cart_line_items_query():
    # attributes of the array of dictionaries: id [make this a counter], customer_name, item_sku, gold, time
    # here I want to join the cart, cart-items, potion_ledger, and potion_catalog
    # from a specific cart I need to get: customer, item, gold, time
    # customer = customer_name found in cart table
    # item = count_to_buy and potion sku from cart_items [make a list of all potions from specific customer]
    # gold = take the total potion of a particular sku multiply by cost from potion_catalog [repeat for all potions]
    # time = from cart_items timestamp
    # return back an array of dictionaries
    with db.engine.begin() as connection:
        cart_items_query = connection.execute(sqlalchemy.text(
            """
            SELECT cart_items.cart_id, 
                    carts.customer_name AS name,
                    cart_items.timestamp AS time, 
                    cart_items.sku AS potion_sku, 
                    cart_items.count_to_buy AS potion_count, 
                    potion_catalog.cost AS cost_of_potion
            FROM cart_items
            JOIN carts ON carts.cart_id = cart_items.cart_id
            JOIN potion_catalog ON cart_items.sku = potion_catalog.sku
            """)).fetchall() #remember each line is a tuple returned where the entire fetchall is an array of tuples
    
    return cart_items_query

def cart_line_items(cart_items_query):
    line_items = []
    counter = 0

    for line in cart_items_query:
        counter +=1
        gold = line[4] * line[5]

        line_items.append(
            {"line_id": counter, "customer_name": line[1], "count_bought": line[4] ,"item_sku": line[3], "line_item_total": gold, "timestamp": line[2]}
        )

    return line_items

def filtering(line_items, customer_name, potion_sku):
    # this function will take in a name and potion one can be a blank str and sort given list of customers
    # returns back an array of dictonaries that is filtered by criteria
    if customer_name == "" or potion_sku == "":
        return line_items

    for line in line_items:
        if line["customer_name"] == customer_name and line["item_sku"] == potion_sku:
            return [line]
        
    return line_items

def sorting_col(line_items, sort_col, sort_order):
    # given an array of dictionaries sort by given sort_col and sort_order
    # return back an array of dictionaries that is sorted by the criteria
    if sort_order == "asc":
        reversing = False
    elif sort_order == "desc":
        reversing = True
    
    return sorted(line_items, key=lambda line: line[sort_col], reverse=reversing)

def pagination_cart_items(line_items, search_page):
    # can only display 5 cart_items at a time
    # returns a next_page_token, pre_page_token, and only 5 items from the line_items
    # TODO what the heck this do
    
    pass

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
    """ """ 

    quantity_to_buy = 0
    # SUM(cart_items.count_to_buy) AS quantity_to_buy
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(
            """
            SELECT carts.cart_id, customer_name, COALESCE(SUM(cart_items.count_to_buy),0) AS quantity_to_buy
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
    with db.engine.begin() as connection:
        for cart_to_buy in cart_info:
            print("checkout: cart_to_buy ", cart_to_buy)
            potion_info = connection.execute(
                sqlalchemy.text( 
                    """
                    SELECT potion_id, cost, sku 
                    FROM potion_catalog
                    WHERE potion_catalog.sku = :sku
                    """
            ), [{"sku": cart_to_buy.sku}]).first()
            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO potion_ledger_entries (potion_id, quantity_delta)
                    VALUES (:potion_id, :quantity)
                    """
            ), [{"potion_id": potion_info.potion_id, "quantity": -cart_to_buy.count_to_buy}])

            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO gold_ledger_entries (gold_delta)
                    VALUES (:gold_change)
                    """
            ), [{"gold_change": cart_to_buy.count_to_buy * potion_info.cost}])

        total_potions_bought += cart_to_buy.count_to_buy
        total_gold_paid += cart_to_buy.count_to_buy * potion_info.cost
        print("checkout: total_potions_bought ", total_potions_bought)
        print("checkout: total_gold_paid ", total_gold_paid)
    
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE carts 
                SET bought = true
                WHERE carts.cart_id = :cart_id
                """
        ), {"cart_id": cart_id})

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
