import azure.functions as func
import json
import os
import requests
import time

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

cache = {
    "data": {},
    "last_fetched": {}
}

CACHE_DURATION = 900  # 15 minutes

LOCATIONS = {
    "vadodara": {"lat": 22.3072, "lon": 73.1812, "currency": "INR", "fuel": {"petrol": "₹94.12", "diesel": "₹90.05"}},
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "currency": "INR", "fuel": {"petrol": "₹104.21", "diesel": "₹92.15"}},
    "delhi": {"lat": 28.6139, "lon": 77.2090, "currency": "INR", "fuel": {"petrol": "₹94.72", "diesel": "₹87.62"}},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "currency": "JPY", "fuel": {"petrol": "¥175", "diesel": "¥150"}},
    "seoul": {"lat": 37.5665, "lon": 126.9780, "currency": "KRW", "fuel": {"petrol": "₩1,600", "diesel": "₩1,450"}}
}

def get_currency_symbol(curr):
    symbols = {"INR": "₹", "JPY": "¥", "KRW": "₩"}
    return symbols.get(curr, curr)

@app.route(route="GetPrices")
def GetPrices(req: func.HttpRequest) -> func.HttpResponse:
    gold_api_key = os.getenv('GOLD_API_KEY')
    if not gold_api_key:
        return func.HttpResponse(
            json.dumps({"error": "GOLD_API_KEY is missing."}),
            mimetype="application/json",
            status_code=500
        )

    # Determine requested location, default to vadodara
    location = req.params.get('location', 'vadodara').lower()
    if location not in LOCATIONS:
        location = 'vadodara'
        
    global cache
    current_time = time.time()
    
    # Return cache if valid for this specific location
    if location in cache["data"] and (current_time - cache["last_fetched"].get(location, 0) < CACHE_DURATION):
        return func.HttpResponse(
            json.dumps(cache["data"][location]),
            mimetype="application/json",
            status_code=200
        )

    loc_data = LOCATIONS[location]
    curr = loc_data["currency"]
    sym = get_currency_symbol(curr)
        
    unified_data = {
        "weather": "Service Unavailable",
        "gold": "Service Unavailable",
        "silver": "Service Unavailable",
        "fuel": loc_data["fuel"],
        "location": location.capitalize()
    }
    
    # 1. Fetch Weather
    try:
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={loc_data['lat']}&longitude={loc_data['lon']}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=auto"
        w_res = requests.get(weather_url, timeout=5)
        if w_res.status_code == 200:
            unified_data["weather"] = w_res.json()
    except Exception:
        pass
        
    # 2. Fetch Gold and Silver from GoldAPI.io
    headers = {
        "x-access-token": gold_api_key,
        "Content-Type": "application/json"
    }
    
    # Fetch Gold (API returns Ounce. Convert to 10g -> 1 Troy Ounce = 3.11034768 * 10 grams)
    try:
        g_res = requests.get(f"https://www.goldapi.io/api/XAU/{curr}", headers=headers, timeout=5)
        if g_res.status_code == 200:
            price_oz = g_res.json().get("price")
            if price_oz:
                price_10g = price_oz / 3.11034768
                unified_data["gold"] = f"{sym}{price_10g:,.2f}"
    except Exception:
        pass
        
    # Fetch Silver (API returns Ounce. Convert to 1kg)
    try:
        s_res = requests.get(f"https://www.goldapi.io/api/XAG/{curr}", headers=headers, timeout=5)
        if s_res.status_code == 200:
            price_oz = s_res.json().get("price")
            if price_oz:
                price_1kg = (price_oz / 31.1034768) * 1000
                unified_data["silver"] = f"{sym}{price_1kg:,.2f}"
    except Exception:
        pass

    # Store in Cache
    cache["data"][location] = unified_data
    cache["last_fetched"][location] = current_time

    return func.HttpResponse(
        json.dumps(unified_data),
        mimetype="application/json",
        status_code=200
    )