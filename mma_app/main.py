from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import asyncio

from .wikipedia_scraper import get_last_fights_and_age
from .ranking import get_fighter_rank
from .model import predict_winner
from .odds import get_upcoming_fights

app = FastAPI()
# Setup templates directory relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Display a list of upcoming fights with model predictions and betting odds.
    Reads the ODDS_API_KEY from environment variables. If provided, calls the
    odds API and computes predictions using MMA Math.
    """
    api_key = os.getenv("ODDS_API_KEY")
    fights_info = []
    if api_key:
        try:
            events = await get_upcoming_fights(api_key)
            for event in events:
                fighters = event.get("fighters")
                if not fighters or len(fighters) != 2:
                    continue
                f1, f2 = fighters
                # Fetch fighter data concurrently in threadpool to avoid blocking
                data_f1, data_f2 = await asyncio.gather(
                    asyncio.to_thread(get_last_fights_and_age, f1),
                    asyncio.to_thread(get_last_fights_and_age, f2),
                )
                prediction = predict_winner(
                    f1, data_f1,
                    f2, data_f2,
                    get_fighter_rank,
                )
                fights_info.append({"event": event, "prediction": prediction})
        except Exception as exc:
            # Log error (print for simplicity)
            print(f"Error fetching fights: {exc}")
  
    return templates.TemplateResponse("index.html", {"request": request, "fights": fights_info})


@app.get("/api/predict")
async def api_predict(fighter_a: str, fighter_b: str):
    """Return JSON prediction for two fighters."""
    data_a = get_last_fights_and_age(fighter_a)
    data_b = get_last_fights_and_age(fighter_b)
    result = predict_winner(fighter_a, data_a, fighter_b, data_b, get_fighter_rank)
    return result
from fastapi.responses import HTMLResponse  # import at top if not already present

@app.get("/ufc319", response_class=HTMLResponse)
async def ufc319(request: Request):
    return templates.TemplateResponse("ufc_319.html", {"request": request})
