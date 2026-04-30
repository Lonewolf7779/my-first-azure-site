import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    # This is a sample response. Later we will add real API calls here.
    prices = {
        "gold": "₹72,450",
        "silver": "₹84,200",
        "petrol_vadodara": "₹94.52",
        "status": "LIVE FROM AZURE"
    }
    
    return func.HttpResponse(
        json.dumps(prices),
        mimetype="application/json",
        status_code=200
    )