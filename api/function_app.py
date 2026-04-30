import azure.functions as func
import json
import os
import requests
import time

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Basic 10-minute in-memory cache to avoid rate limits
cache = {
    "data": None,
    "last_fetched": 0
}

CACHE_DURATION = 600  # 10 minutes in seconds

@app.route(route="GetPrices")
def GetPrices(req: func.HttpRequest) -> func.HttpResponse:
    gold_api_key = os.getenv('GOLD_API_KEY')
    if not gold_api_key:
        return func.HttpResponse(
            json.dumps({"error": "GOLD_API_KEY is missing."}),
            mimetype="application/json",
            status_code=500
        )

    global cache
    current_time = time.time()
    
    # Return matched cache if valid
    if cache["data"] and (current_time - cache["last_fetched"] < CACHE_DURATION):
        return func.HttpResponse(
            json.dumps(cache["data"]),
            mimetype="application/json",
            status_code=200
        )
        
    unified_data = {
        "weather": "Service Unavailable",
        "gold": "Service Unavailable",
        "silver": "Service Unavailable",
        "fuel": {"petrol": "₹94.12", "diesel": "₹90.05"} # Mock fuel data
    }
    
    # 1. Fetch Weather (Open-Meteo Vadodara)
    try:
        weather_url = 'https://api.open-meteo.com/v1/forecast?latitude=22.3072&longitude=73.1812&current_weather=true&hourly=uv_index&timezone=Asia%2FKolkata'
        w_res = requests.get(weather_url, timeout=5)
        if w_res.status_code == 200:
            unified_data["weather"] = w_res.json()
    except Exception as e:
        pass
        
    # 2. Fetch Gold and Silver from GoldAPI.io
    headers = {
        "x-access-token": gold_api_key,
        "Content-Type": "application/json"
    }
    
    # Fetch Gold
    try:
        g_res = requests.get("https://www.goldapi.io/api/XAU/INR", headers=headers, timeout=5)
        if g_res.status_code == 200:
            gold_price = g_res.json().get("price")
            if gold_price:
                unified_data["gold"] = f"₹{gold_price:,.2f}"
    except Exception:
        pass
        
    # Fetch Silver
    try:
        s_res = requests.get("https://www.goldapi.io/api/XAG/INR", headers=headers, timeout=5)
        if s_res.status_code == 200:
            silver_price = s_res.json().get("price")
            if silver_price:
                unified_data["silver"] = f"₹{silver_price:,.2f}"
    except Exception:
        pass

    # Store in Cache
    cache["data"] = unified_data
    cache["last_fetched"] = current_time

    return func.HttpResponse(
        json.dumps(unified_data),
        mimetype="application/json",
        status_code=200
    )