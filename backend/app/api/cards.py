from fastapi import APIRouter, HTTPException, Query
from app.services.scryfall import ScryfallService
from app.schemas.card import CardResponse, BulkCardRequest
from typing import List

router = APIRouter(prefix="/cards", tags=["Cards"])

# Start Scryfall Service
card_service = ScryfallService()

@router.get("/ping")
async def ping_card():
    return {"status":"Card router is working"}

@router.get("/search", response_model=CardResponse)
async def search_card(name: str = Query(..., description="Name of the card to search")):
    card_data = await card_service.fetch_full_card(card=name)
    if not card_data:
        raise HTTPException(status_code=404, detail=f"'{name}' was not found")
    
    return CardResponse(
        name = card_data["name"],
        id = card_data["id"],
        image_url = card_data["image_url"],
        mana_cost = card_data["mana_cost"],
        cmc = card_data["cmc"],
        type = card_data["type"],
        colors = card_data["colors"],
        oracle_text = card_data["oracle_text"],
        keywords = card_data["keywords"],
        legality = card_data["legality"]
        )

@router.get("bulk")