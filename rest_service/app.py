from collections import defaultdict
from statistics import mean
from fastapi import Body, FastAPI, Depends, HTTPException
import requests
from sqlalchemy.orm import Session
from typing import List
import time
from datetime import datetime, timedelta
import os
from schemas import CoinByRange



app = FastAPI()

# Create database tables


def coin_data_range(coin_id, startDate, endDate):
    """
    Fetch historical coin market data within a date range.

    Args:
        coin_id (str): The ID of the coin.
        startDate (str): The start date in "YYYY-MM-DD" format.
        endDate (str): The end date in "YYYY-MM-DD" format.

    Returns:
        dict: Market data for the specified range or error message.
    """
    # Convert dates to UNIX timestamps
    start_timestamp = int(datetime.strptime(startDate, "%Y-%m-%d").timestamp())
    end_timestamp = int(datetime.strptime(endDate, "%Y-%m-%d").timestamp())

    # API URL and parameters
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {
        "vs_currency": 'usd',
        "from": start_timestamp,
        "to": end_timestamp
    }

    # Make the request
    response = requests.get(url, params=params)

    if response.status_code == 200:
        # Parse and return data
        data = response.json()
        return data
    else:
        # Handle errors
        print(f"Error: {response.status_code}, Message: {response.text}")
        return {"error": response.status_code, "message": response.text}
    



@app.post("/aboutcoin/")
def about_coin(coin: CoinByRange=Body(...)):
    """
    Get historical market data for a coin within a specific date range.
    """
    # Validate input dates
    try:
        datetime.strptime(coin.startDate, "%Y-%m-%d")
        datetime.strptime(coin.endDate, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use 'YYYY-MM-DD'.")

    # Call the coin_data_range function
    data = coin_data_range(coin.coin_id, coin.startDate, coin.endDate)

    # Handle errors from the function
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])

    prices = data.get("prices", [])


    price_values = [price[1] for price in prices]
    timestamps = [price[0] for price in prices]
    if not prices:
        raise HTTPException(status_code=400, detail="No price data available for the given range.")
    # Calculate avg, max, and min prices
    avg_price = mean(price_values)
    max_price = max(price_values)
    min_price = min(price_values)

     # Find the timestamps corresponding to the max and min prices
    max_price_index = price_values.index(max_price)
    min_price_index = price_values.index(min_price)

    # Convert timestamps to datetime
    max_price_date = datetime.utcfromtimestamp(timestamps[max_price_index] / 1000).strftime("%Y-%m-%d %H:%M:%S")
    min_price_date = datetime.utcfromtimestamp(timestamps[min_price_index] / 1000).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "avg_price": avg_price,
        "max_price": max_price,
        "max_price_date": max_price_date,
        "min_price": min_price,
        "min_price_date": min_price_date
    }
@app.post("/aboutcoinDaily/")
def about_coin(coin: CoinByRange):
    """
    Get historical market data for a coin within a specific date range.
    """
    # Validate input dates
    try:
        datetime.strptime(coin.startDate, "%Y-%m-%d")
        datetime.strptime(coin.endDate, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use 'YYYY-MM-DD'.")

    # Call the coin_data_range function
    data = coin_data_range(coin.coin_id, coin.startDate, coin.endDate)

    # Handle errors from the function
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])
    # Extract prices and their timestamps
    prices = data.get("prices", [])

    if not prices:
        raise HTTPException(status_code=400, detail="No price data available for the given range.")

    # Group prices by date (day)
    daily_prices = defaultdict(list)
    
    for timestamp, price in prices:
        # Convert timestamp to datetime object
        date = datetime.fromtimestamp(timestamp/1000 ).date()
        print(date)
        print (price)
        
        daily_prices[date].append(price)
        


    
    # Calculate avg, max, and min for each day
    daily_stats = []
    for date, price_list in daily_prices.items():
        avg_price = mean(price_list)
        max_price = max(price_list)
        min_price = min(price_list)
        daily_stats.append({
            "date": date.strftime("%Y-%m-%d"),
            "avg_price": avg_price,
            "max_price": max_price,
            "min_price": min_price
        })
    return daily_stats