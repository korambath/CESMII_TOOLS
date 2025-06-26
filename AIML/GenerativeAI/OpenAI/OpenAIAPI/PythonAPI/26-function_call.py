import datetime
from zoneinfo import ZoneInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz
import json
import requests
import os


def get_current_time(city: str) -> dict:
    try:
        # Get coordinates for the city
        geolocator = Nominatim(user_agent="time_finder")
        location = geolocator.geocode(city)
        
        if not location:
            return {"error": "City not found"}

        # Get timezone based on coordinates
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        
        if not timezone_str:
            return {"error": "Timezone not found"}

        # Get current time in that timezone
        timezone = pytz.timezone(timezone_str)
        current_time = datetime.now(timezone)

        return {
            "city": city,
            "timezone": timezone_str,
            "local_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {"error": str(e)}


def get_weather(location: str) -> dict:
    try:
        # Step 1: Get coordinates from city name
        geolocator = Nominatim(user_agent="weather_finder")
        geo_data = geolocator.geocode(location)
        
        if not geo_data:
            return {"error": "City not found"}

        latitude = geo_data.latitude
        longitude = geo_data.longitude

        # Step 2: Fetch weather data from Open-Meteo API
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
            f"&temperature_unit=fahrenheit"
        )

        response = requests.get(url)
        data = response.json()

        if "current" not in data:
            return {"error": "Weather data unavailable"}

        current = data["current"]

        return {
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "temperature_f": current.get("temperature_2m"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_mph": current.get("wind_speed_10m")
        }

    except Exception as e:
        return {"error": str(e)}

city = "Los Angeles"
print (get_current_time(city))
print (get_weather(city))
