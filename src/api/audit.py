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
    result = execute_sql("SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory")
    nums_potions = result.num_red_potions + result.num_green_potions + result.num_blue_potions

    print("get_inventory: red_potions ", result.num_red_potions)
    print("get_inventory: green_potions ", result.num_green_potions)
    print("get_inventory: blue_potions ", result.num_blue_potions)

    result = execute_sql("SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory") 
    ml_per_barrel = result.num_red_ml + result.num_green_ml + result.num_blue_ml

    print("get_inventory: red_ml ", result.num_red_ml)
    print("get_inventory: green_ml ", result.num_green_ml)
    print("get_inventory: blue_ml ", result.num_blue_ml)

    result = execute_sql("SELECT gold FROM global_inventory")
    gold_total = result.gold

    print("get_inventory: gold_total ", gold_total)
    print("get_inventory: ml_per_barrel ", ml_per_barrel)
    print("get_inventory: nums_potions ", nums_potions)
    
    return {"number_of_potions": nums_potions, "ml_in_barrels": ml_per_barrel, "gold": gold_total}

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
