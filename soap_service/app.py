from fastapi import Depends, HTTPException
from spyne import Application, rpc, ServiceBase, Iterable, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
import requests
from datetime import datetime

from models import Coin, Base
from database import engine, get_db

BASE_URL = "https://api.coingecko.com/api/v3"
Base.metadata.create_all(bind=engine)
class CoinService(ServiceBase):
    @rpc(_returns=Iterable(Unicode))
    def get_trending_coins(ctx):
        """Fetch trending coins from the external API and save to database."""
        db = next(get_db())  # Manually fetch the database session
        try:
            url = f"{BASE_URL}/search/trending"
            response = requests.get(url)
            if response.status_code == 200:
                now = datetime.now().date()
                coins_added = []
                JsonResponse = response.json().get("coins", [])
                for coin in JsonResponse:
                    coin_name = coin["item"]["name"]
                    coin_id = coin["item"]["id"]

                    # Check if the coin already exists
                    existing_coin = db.query(Coin).filter(
                        Coin.coin_id == coin_id,
                        Coin.trending_date == now.strftime("%Y-%m-%d")
                    ).first()

                    if existing_coin:
                        print(f"Coin with ID {coin_id} and date {now} already exists. Skipping.")
                        continue  # Skip if the coin already exists

                    db_coin = Coin(
                        coin_id=coin_id,
                        trending_date=now.strftime("%Y-%m-%d"),  # Format date to match database type
                        coin_name=coin_name
                    )
                    print("Adding coin to DB:", db_coin)

                    db.add(db_coin)
                    try:
                        db.commit()
                        db.refresh(db_coin)
                        coins_added.append(db_coin)
                    except Exception as e:
                        db.rollback()
                        print(f"Error adding coin {coin_id}: {e}")
                        raise Exception("Could not create coin entry.") from e

                coins = [coin["item"]["name"] for coin in JsonResponse]
                return coins
            else:
                return [f"Error: {response.status_code}, {response.text}"]
        finally:
            db.close()
        
    @rpc(Unicode, Unicode, Unicode, _returns=Unicode)
    def coin_data_range(ctx, coin_id, start_date, end_date):
        """Fetch historical coin market data within a date range."""
        try:
            # Convert dates to UNIX timestamps
            start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

            # API URL and parameters
            url = f"{BASE_URL}/coins/{coin_id}/market_chart/range"
            params = {
                "vs_currency": 'usd',
                "from": start_timestamp,
                "to": end_timestamp
            }

            # Make the request
            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                return str(data)  # Return data as string
            else:
                return f"Error: {response.status_code}, Message: {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

# SOAP application
soap_app = Application(
    [CoinService],
    'coin.soap.service',
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

app = WsgiApplication(soap_app)

if __name__ == '__main__':
    # Run the WSGI server on port 5001 (or any port you prefer)
    with make_server('localhost', 5001, app) as server:
        print("Server running on http://localhost:5001")
        server.serve_forever()
