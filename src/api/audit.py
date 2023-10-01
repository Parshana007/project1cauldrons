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
    result = execute_sql("SELECT num_red_potions FROM global_inventory")
    nums_red_potions = result.num_red_potions
    result = execute_sql("SELECT ml_in_barrels FROM global_inventory") 
    ml_per_barrel = result.num_red_ml
    result = execute_sql("SELECT gold FROM global_inventory")
    gold_total = result.gold
    
    return {"number_of_potions": nums_red_potions, "ml_in_barrels": ml_per_barrel, "gold": gold_total}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
