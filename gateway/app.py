import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from zeep import Client

app = FastAPI()

# Define the endpoints for each service
SOAP_SERVICE_URL = "http://localhost:5001"  # URL for SOAP service
REST_SERVICE_URL = "http://localhost:8002"  # URL for REST service
GRAPHQL_SERVICE_URL = "http://localhost:8001/graphql"  # URL for GraphQL service
class CoinByRange(BaseModel):
    coin_id: str
    startDate: str
    endDate: str

@app.get("/soap/trending")
async def get_trending_from_soap():
    """
    Proxy request to SOAP service for trending coins.
    """
    soap_body = """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:coin="coin.soap.service">
        <soapenv:Header/>
        <soapenv:Body>
            <coin:get_trending_coins/>
        </soapenv:Body>
    </soapenv:Envelope>"""

    headers = {
        "Content-Type": "text/xml"  # Required for SOAP requests
    }

    try:
        # Make a POST request to the SOAP service
        response = requests.post(SOAP_SERVICE_URL, data=soap_body, headers=headers)

        # Check if the response is successful
        if response.status_code == 200:
            # Parse and return the response (you may need to adjust based on actual response structure)
            return {"trending_coins": response.text}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.post("/graphql/aboutCoin/")
async def graphql_about_coin(coin: CoinByRange):
    """
    Forward request to GraphQL service for aboutCoin query.
    """
    query = """
    query($coin_id: String!, $startDate: String!, $endDate: String!) {
      aboutCoin(coin_id: $coin_id, startDate: $startDate, endDate: $endDate) {
        avg_price
        max_price
        max_price_date
        min_price
        min_price_date
      }
    }
    """
    
    variables = {
        "coin_id": coin.coin_id,
        "startDate": coin.startDate,
        "endDate": coin.endDate
    }

    try:
        response = requests.post(
            GRAPHQL_SERVICE_URL,
            json={"query": query, "variables": variables}
        )

        if response.status_code == 200:
            return response.json()  # Return the data from GraphQL
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graphql/aboutCoinDaily/")
async def graphql_about_coin_daily(coin: CoinByRange):
    """
    Forward request to GraphQL service for aboutCoinDaily query.


    
    """
    query = """
    query {
        aboutCoinDaily(coin_id: \"""" + coin.coin_id + """\", startDate: \"""" + coin.startDate + """\", endDate: \"""" + coin.endDate + """\") {
            date
            avg_price
            max_price
            min_price
        }
    }
    """
    


    try:
        response = requests.post(
            GRAPHQL_SERVICE_URL,
            json={"query": query}
        )

        if response.status_code == 200:
            return response.json()  # Return the data from GraphQL
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/aboutcoin/")
def about_coin(coin: CoinByRange):
    """
    Fetch historical market data for a coin from the REST service.
    """
    try:
        # Forward the request to the REST service
        response = requests.post(
            f"{REST_SERVICE_URL}/aboutcoin/",
            json=coin.dict()  # Convert the input Pydantic model to JSON
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/aboutcoinDaily/")
def about_coin_daily(coin: CoinByRange):
    """
    Fetch daily historical market data for a coin from the REST service.
    """
    try:
        # Forward the request to the REST service
        response = requests.post(
            f"{REST_SERVICE_URL}/aboutcoinDaily/",
            json=coin.dict()  # Convert the input Pydantic model to JSON
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))