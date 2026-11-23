import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

def geocode_place(place_name: str) -> dict | None:
    """Converts a city or landmark into lat/lon using Geoapify API."""
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text": place_name,
        "limit": 1,
        "apiKey": GEOAPIFY_API_KEY,
    }
    try:
        res = requests.get(url, params=params, timeout=10).json()
        features = res.get("features", [])
        if features:
            props = features[0]["properties"]
            return {
                "name": place_name,
                "lat": float(props["lat"]),
                "lon": float(props["lon"]),
            }
    except Exception as e:
        print(f"Geoapify error for {place_name}: {e}")
    return None

def get_live_weather(destination: str) -> str:
    """Fetches a 5-day / 3-hour forecast using OpenWeatherMap API."""
    coords = geocode_place(destination)
    if not coords:
        return f"Could not find coordinates for {destination}."

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": coords["lat"],
        "lon": coords["lon"],
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    try:
        res = requests.get(url, params=params, timeout=10).json()
        forecasts = res.get("list", [])
        if not forecasts:
            return f"Weather data unavailable: {res.get('message', 'Unknown error')}"

        # Pick one midday snapshot per day (every 8th 3-hour block)
        lines = [f"5-Day Live Weather Forecast for {destination}:"]
        for entry in forecasts[::8]:
            date_str = entry["dt_txt"].split(" ")[0]
            temp = entry["main"]["temp"]
            desc = entry["weather"][0]["description"].capitalize()
            rain_prob = int(entry.get("pop", 0) * 100)
            lines.append(f"- {date_str}: {temp}°C, {desc} | Rain chance: {rain_prob}%")
        return "\n".join(lines)
    except Exception as e:
        return f"Weather API error: {e}"

def geocode_itinerary_spots(spots: list[dict]) -> list[dict]:
    """Attaches lat/lon coordinates to each day's landmark for the Leaflet map."""
    pinned = []
    for item in spots:
        geo = geocode_place(item["place"])
        if geo:
            pinned.append({
                "day": item["day"],
                "place": item["place"],
                "lat": geo["lat"],
                "lon": geo["lon"],
            })
    return pinned