from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("TRUNCATE gold_ledger_entries")) #clears the gold_ledger_entries table
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger_entries (gold_delta) VALUES (100)"))
        connection.execute(sqlalchemy.text("TRUNCATE barrel_ledger_entries")) #clears the barrel_ledger_entries table
        # connection.execute(sqlalchemy.text("INSERT INTO barrel_ledger_entries (red_ml_delta, blue_ml_delta, green_ml_delta, dark_ml_delta) VALUES (0, 0, 0, 0)"))
        connection.execute(sqlalchemy.text("TRUNCATE potion_ledger_entries")) #clears the potion_ledger_entries table
        # connection.execute(sqlalchemy.text("INSERT INTO potion_ledger_entries (potion_delta) VALUES (0)"))

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    return {
        "shop_name": "Cabybara Cauldron",
        "shop_owner": "Parshana Sekhon",
    }

