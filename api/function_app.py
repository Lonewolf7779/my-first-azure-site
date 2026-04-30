import azure.functions as func
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="GetPrices")
def GetPrices(req: func.HttpRequest) -> func.HttpResponse:
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