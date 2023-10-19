from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

def execute_sql(query):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(query))
        return result.first()

@router.get("/inventory")
def get_inventory():
    """ """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT SUM(gold_delta) total_gold FROM gold_ledger_entries")).first()
        gold_total = result.total_gold
        result = connection.execute(sqlalchemy.text(
            """SELECT COALESCE(SUM(red_ml_delta), 0) total_red_ml, COALESCE(SUM(blue_ml_delta)) total_blue_ml, COALESCE(SUM(green_ml_delta)) total_green_ml, COALESCE(SUM(dark_ml_delta), 0) total_dark_ml
            FROM barrel_ledger_entries
            """)
        ).first()
        ml_per_barrel = result.total_red_ml + result.total_green_ml + result.total_blue_ml + result.total_dark_ml
        result = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(quantity_delta), 0) total_potions FROM potion_ledger_entries")).first()
        total_potions = result.total_potions
    
    return {"number_of_potions": total_potions, "ml_in_barrels": ml_per_barrel, "gold": gold_total}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print("post_audit_results: audit_explanation", audit_explanation)

    return "OK"
