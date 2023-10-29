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

    params = {}
    page_size = 5

    sql_to_execute = """
    SELECT cart_items.entry_id AS entry_id,
        cart_items.cart_id, 
        carts.customer_name AS customer_name,
        cart_items.timestamp AS timestamp, 
        cart_items.count_to_buy AS potion_count, 
        potion_catalog.cost AS cost_of_potion,
        cart_items.count_to_buy,
        CONCAT(cart_items.count_to_buy, ' ', cart_items.sku) AS item_sku, 
        cart_items.count_to_buy * potion_catalog.cost AS line_item_total
    FROM cart_items
    JOIN carts ON carts.cart_id = cart_items.cart_id
    JOIN potion_catalog ON cart_items.sku = potion_catalog.sku
    """

    # FILTERING
    if customer_name != "":
        customer_name_param = '%' + customer_name + '%'
        sql_to_execute += "WHERE customer_name ILIKE :customer_name_param"
        params["customer_name_param"] = customer_name_param
    if potion_sku != "":
        potion_name_param = '%' + potion_sku + '%'
        if "WHERE" not in sql_to_execute:
            sql_to_execute += "WHERE potion_catalog.sku ILIKE :potion_name_param"
        else:
            sql_to_execute += " AND potion_catalog.sku ILIKE :potion_name_param"
        params["potion_name_param"] = potion_name_param

    # SORTING
    sql_to_execute +=  " " + "ORDER BY " + sort_col + " " + sort_order.upper() + " "

    # sql_to_execute += "ORDER BY :sorting_col :sorting_direc"
    # params["sorting_col"] = sort_col
    # params["sorting_direc"] = sort_order.upper()

    

    with db.engine.begin() as connection:
        # PAGINATION
        # count_rows = connection.execute(sqlalchemy.text("SELECT COUNT(*) total_rows FROM cart_items")).first()
        # print("count_rows.total_rows", count_rows.total_rows)

        if search_page == "":
            search_page = 0
        else: 
            search_page = int(search_page)
    
        start_index = search_page * page_size
        end_index = start_index + page_size

        # if end_index + 1 >= count_rows.total_rows:
        #     end_index = count_rows.total_rows
        #     next_page = ""
        # else:
        #     next_page = str(search_page + 1)

        if search_page == 0:
            prev_page = ""
        else:
            prev_page = str(search_page - 1)

        print(start_index)

        sql_to_execute += "LIMIT 5 OFFSET :offset"
        params["offset"] = start_index


        sql_result = connection.execute(sqlalchemy.text(sql_to_execute), params).fetchall() 

        if len(sql_result) < 5:
            next_page = ""
        else:
            next_page = str(search_page + 1)

        print("len(sql_result)", len(sql_result))
        print(prev_page)
        print(next_page)

    final_result_items = []

    for line in sql_result:
        final_result_items.append({
                "line_item_id": line.entry_id,
                "item_sku": line.item_sku, # sku + count_to_buy
                "customer_name": line.customer_name, 
                "line_item_total": line.line_item_total, #gold
                "timestamp": line.timestamp,
        })

    return {
        "previous": prev_page,
        "next": next_page,
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


def pagination_cart_items(line_items, search_page):

    # assume search_page is a string now but is the string form of an int 
    # 1. convert to int
    # 2. page_size = 5 bc can only display 5 items at a time
    # 3. find the range from the start index to the last index with the page size
    # ex. if there are 14 things then when search_page = 0 then [1, 2, 3, 4, 5] are displayed when search_page = 1 then [6, 7, 8, 9, 10] displayed
    # ex. seach_page = 2 [11, 12, 13, 14]
    # ex. next_page = search_page + 1 since there are still 5 more thing to display and pre_page = search_page - 1 or the current one
    # 4. calculate the next_page, and prev_page return these values
    # 5. return the slicing of what can currently pass in...
    
    if search_page == "":
        search_page = 0
    else: 
        search_page = int(search_page)
    
    page_size = 5
    start_index = search_page * page_size
    end_index = start_index + page_size

    if end_index + 1 >= len(line_items):
        end_index = len(line_items) 
        next_page = ""
    else:
        next_page = str(search_page + 1)

    if search_page == 0:
        prev_page = ""
    else:
        prev_page = str(search_page - 1)

    return prev_page, next_page, line_items[start_index:end_index]






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
