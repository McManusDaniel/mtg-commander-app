from fastapi import FastAPI
from app.api import cards

app = FastAPI(title="MTC Commander API")
app.include_router(cards.router)

@app.get("/")
async def root():
    return {"message": "MTC Commander API is live!"}