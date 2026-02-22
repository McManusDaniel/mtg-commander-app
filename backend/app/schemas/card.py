from pydantic import BaseModel
from typing import list

class CardResponse(BaseModel):
    name: str
    id: str
    image_url: dict | None
    mana_cost: str
    cmc: int
    type: str
    colors: list
    oracle_text: str
    keywords: list
    legality: str
    
class BulkCardRequest(BaseModel):
    names: list[str]