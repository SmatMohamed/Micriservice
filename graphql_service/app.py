from datetime import datetime
import requests
import matplotlib.dates as mdates
import io
import os
import matplotlib.pyplot as plt
from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL

# Define type resolvers
query = QueryType()

# REST service URL
REST_SERVICE_BASE_URL = "http://localhost:8002"

# Helper function to generate a chart (matplotlib)
def generate_chart(prices, timestamps, chart_type="line"):
    """
    Generate a chart from the provided prices and timestamps.
    Saves the chart as a PNG file and returns the file path.
    """
    fig, ax = plt.subplots()

    # Plot the prices over time
    ax.plot(timestamps, prices, label="Price")

    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.set_title("Coin Price Over Time")
    ax.legend()

    # Define the path where to save the image
    image_dir = "charts"
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    # Generate a unique filename for each chart
    image_path = os.path.join(image_dir, "chart.png")

    # Save the chart image to the disk
    plt.savefig(image_path, format="png")
    plt.close(fig)

    return image_path

# Resolver for `aboutCoin`
@query.field("aboutCoin")
def resolve_about_coin(_, info, coin_id, startDate, endDate):
    url = f"{REST_SERVICE_BASE_URL}/aboutcoin/"
    payload = {"coin_id": coin_id, "startDate": startDate, "endDate": endDate}
    response = requests.post(url, json=payload)

    print(f"REST Service Response: {response.status_code} - {response.text}")  # Debugging line

    if response.status_code != 200:
        raise Exception(f"REST service error: {response.status_code} - {response.text}")

    data = response.json()

    print(f"Response JSON: {data}")  # Debugging line

    # Extract the relevant fields
    avg_price = data.get("avg_price")
    max_price = data.get("max_price")
    max_price_date = data.get("max_price_date")
    min_price = data.get("min_price")
    min_price_date = data.get("min_price_date")

    # Check if the data is valid
    if avg_price is None or max_price is None or min_price is None:
        return {"error": "Incomplete data from REST service"}

    # If you still want a chart based on some synthetic data (e.g., from the available prices)
    # you could use this for chart generation (here, I'm using dummy data to generate a chart)
    chart_image = generate_chart([ min_price, max_price], [ min_price_date ,max_price_date ])

    return {
        "avg_price": avg_price,
        "max_price": max_price,
        "max_price_date": max_price_date,
        "min_price": min_price,
        "min_price_date": min_price_date,
        "chart_image": chart_image  # Include chart image in the response
    }


# Resolver for `aboutCoinDaily`
@query.field("aboutCoinDaily")
def resolve_about_coin_daily(_, info, coin_id, startDate, endDate):
    url = f"{REST_SERVICE_BASE_URL}/aboutcoinDaily/"
    payload = {"coin_id": coin_id, "startDate": startDate, "endDate": endDate}
    print (payload)
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        raise Exception(f"REST service error: {response.status_code} - {response.text}")

    data = response.json()
    about_coin_daily_data=data
    # Parse the data
    dates = [datetime.strptime(item["date"], "%Y-%m-%d") for item in about_coin_daily_data]
    avg_prices = [item["avg_price"] for item in about_coin_daily_data]
    max_prices = [item["max_price"] for item in about_coin_daily_data]
    min_prices = [item["min_price"] for item in about_coin_daily_data]

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(dates, avg_prices, label='Avg Price', color='blue', marker='o')
    plt.plot(dates, max_prices, label='Max Price', color='green', marker='o')
    plt.plot(dates, min_prices, label='Min Price', color='red', marker='o')

    # Format the date on x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gcf().autofmt_xdate()

    # Add labels and title
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title('{coin_id} Price Analysis (Daily)')
    plt.legend()

    # Save the plot as an image file
    image_path = '{coin_id}_price_analysis.png'
    plt.savefig(image_path)

    # Display the plot
    plt.show()

# Return the image path if needed (e.g., for API response or front-end)
    print(f"Chart saved to: {image_path}")

    # Ensure the data is a list
    if isinstance(data, list):
        return data  # Return the list of daily stats directly
    else:
        raise Exception(f"Expected list, but received: {type(data)}")



# Load GraphQL schema
type_defs = """
type CoinStats {
  avg_price: Float
  max_price: Float
  max_price_date: String
  min_price: Float
  min_price_date: String
  chart_image: String
}

type DailyStats {
    date: String
    avg_price: Float
    max_price: Float
    min_price: Float
}

type Query {
  aboutCoin(coin_id: String!, startDate: String!, endDate: String!): CoinStats
  aboutCoinDaily(coin_id: String, startDate: String, endDate: String): [DailyStats]
}
"""

# Create executable schema
schema = make_executable_schema(type_defs, query)

# Setup GraphQL application
app = GraphQL(schema)
