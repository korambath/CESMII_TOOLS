import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from anthropic import Anthropic, beta_tool
from dotenv import load_dotenv

# --------------------------------------------------
# 1. Load environment variables
# --------------------------------------------------

load_dotenv(Path.home() / ".config" / ".env")

# Initialize Anthropic client
client = Anthropic()


def detect_server_timezone() -> str:
    """Detect the IANA timezone name of the machine running Python."""
    tz_env = os.environ.get("TZ")
    if tz_env:
        try:
            ZoneInfo(tz_env)
            return tz_env
        except ZoneInfoNotFoundError:
            pass

    # macOS / most Linux: /etc/localtime -> .../zoneinfo/Area/City
    try:
        target = os.path.realpath("/etc/localtime")
        if "zoneinfo/" in target:
            return target.split("zoneinfo/", 1)[1]
    except OSError:
        pass

    return "UTC"


# Automatically detect the timezone of the machine running Python
server_time_zone = detect_server_timezone()
preferred_time_zone = server_time_zone

# Abort any HTTP request that takes longer than this (seconds)
FETCH_TIMEOUT_S = 15

print(f"\nServer timezone detected: {server_time_zone}")


def format_full(now: datetime, tz_name: str) -> str:
    """Approximate Intl.DateTimeFormat dateStyle 'full' + timeStyle 'long'.

    e.g. "Saturday, October 31, 2026 at 10:15:30 AM PDT"
    """
    t = now.astimezone(ZoneInfo(tz_name))
    hour12 = t.hour % 12 or 12
    return (
        f"{t:%A}, {t:%B} {t.day}, {t.year} at "
        f"{hour12}:{t:%M:%S} {t:%p} {t:%Z}"
    )


# --------------------------------------------------
# 2. Geocoding function
# --------------------------------------------------

def get_coordinates(location: str) -> dict | None:
    response = httpx.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": location, "format": "json", "limit": "1"},
        headers={"User-Agent": "weather_finder/1.0"},
        timeout=FETCH_TIMEOUT_S,
    )

    if response.status_code != 200:
        raise RuntimeError("Geocoding service unavailable")

    data = response.json()

    if not isinstance(data, list) or len(data) == 0:
        return None

    return {
        "latitude": float(data[0]["lat"]),
        "longitude": float(data[0]["lon"]),
    }


# --------------------------------------------------
# 3. Get current weather
# --------------------------------------------------

def get_weather_data(location: str, preferred_tz: str) -> dict:
    try:
        # Get coordinates
        coordinates = get_coordinates(location)

        if not coordinates:
            return {"error": f"City not found: {location}"}

        latitude = coordinates["latitude"]
        longitude = coordinates["longitude"]

        # Open-Meteo API
        response = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "timezone": "auto",
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
            },
            timeout=FETCH_TIMEOUT_S,
        )

        if response.status_code != 200:
            raise RuntimeError("Weather API request failed")

        data = response.json()

        if not data.get("current"):
            return {"error": "Weather data unavailable"}

        current = data["current"]
        # Capture the current instant once
        now = datetime.now(timezone.utc)

        return {
            "location": location,
            "latitude": latitude,
            "longitude": longitude,

            # Timezone information
            "city_timezone": data["timezone"],
            "city_timezone_abbreviation": data.get("timezone_abbreviation"),
            "server_timezone": server_time_zone,
            "preferred_timezone": preferred_tz,

            # Actual current time, formatted independently
            "city_current_time": format_full(now, data["timezone"]),
            "preferred_current_time": format_full(now, preferred_tz),
            "server_current_time": format_full(now, server_time_zone),

            # Keep this separately as the observation timestamp
            "weather_observation_time": current["time"],

            # Actual weather
            "temperature_f": current["temperature_2m"],
            "humidity_percent": current["relative_humidity_2m"],
            "precipitation_mm": current["precipitation"],
            "wind_speed_mph": current["wind_speed_10m"],
        }

    except Exception as error:
        print("Weather error:", error)
        return {"error": str(error) or "Unable to retrieve weather data"}


# --------------------------------------------------
# 4. Get weather forecast for the next 3 days
# --------------------------------------------------

def get_forecast_data(location: str, preferred_tz: str) -> dict:
    try:
        # Get coordinates
        coordinates = get_coordinates(location)

        if not coordinates:
            return {"error": f"City not found: {location}"}

        latitude = coordinates["latitude"]
        longitude = coordinates["longitude"]

        # Open-Meteo forecast API
        response = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "timezone": "auto",
                "latitude": latitude,
                "longitude": longitude,
                # Daily forecast parameters
                "daily": ",".join([
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                    "weather_code",
                ]),
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "forecast_days": "3",
            },
            timeout=FETCH_TIMEOUT_S,
        )

        if response.status_code != 200:
            raise RuntimeError("Forecast API request failed")

        data = response.json()

        if not data.get("daily"):
            return {"error": "Forecast data unavailable"}

        daily = data["daily"]

        # Convert each date into a reliable weekday name
        # (a plain calendar date, independent of any timezone)
        forecast = [
            {
                "date": date,
                "day_of_week": datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
                "temperature_max_f": daily["temperature_2m_max"][i],
                "temperature_min_f": daily["temperature_2m_min"][i],
                "precipitation_mm": daily["precipitation_sum"][i],
                "precipitation_probability_percent": daily["precipitation_probability_max"][i],
                "wind_speed_max_mph": daily["wind_speed_10m_max"][i],
                "weather_code": daily["weather_code"][i],
            }
            for i, date in enumerate(daily["time"])
        ]

        return {
            "location": location,
            "latitude": latitude,
            "longitude": longitude,

            "city_timezone": data["timezone"],
            "city_timezone_abbreviation": data.get("timezone_abbreviation"),

            "server_timezone": server_time_zone,
            "preferred_timezone": preferred_tz,

            "forecast": forecast,
        }

    except Exception as error:
        print("Forecast error:", error)
        return {"error": str(error) or "Unable to retrieve forecast"}


# --------------------------------------------------
# 5. Get local time for any city
# --------------------------------------------------

def get_time_of_day_data(location: str, preferred_tz: str) -> dict:
    try:
        # Resolve city coordinates
        coordinates = get_coordinates(location)

        if not coordinates:
            return {"error": f"City not found: {location}"}

        latitude = coordinates["latitude"]
        longitude = coordinates["longitude"]

        # Ask Open-Meteo for the city's timezone
        response = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m",
                "timezone": "auto",
            },
            timeout=FETCH_TIMEOUT_S,
        )

        if response.status_code != 200:
            raise RuntimeError("Unable to retrieve city timezone")

        data = response.json()

        if not data.get("timezone"):
            return {"error": "City timezone unavailable"}

        # Capture one exact current instant
        now = datetime.now(timezone.utc)

        # Format time in the requested city's and user's preferred timezones
        city_time = format_full(now, data["timezone"])
        user_time = format_full(now, preferred_tz)

        # Determine time of day in the requested city
        city_hour = now.astimezone(ZoneInfo(data["timezone"])).hour

        if 5 <= city_hour < 12:
            time_of_day = "Morning"
        elif 12 <= city_hour < 17:
            time_of_day = "Afternoon"
        elif 17 <= city_hour < 21:
            time_of_day = "Evening"
        else:
            time_of_day = "Night"

        return {
            "location": location,
            "latitude": latitude,
            "longitude": longitude,

            "city_timezone": data["timezone"],
            "city_time": city_time,
            "preferred_timezone": preferred_tz,
            "preferred_time": user_time,

            "time_of_day": time_of_day,
            "hour_24": city_hour,

            "timestamp_utc": now.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        }

    except Exception as error:
        print("Time error:", error)
        return {"error": str(error) or "Unable to retrieve local time"}


# --------------------------------------------------
# 6. Get weather alerts for the next 3 days
# --------------------------------------------------
#
# Open-Meteo has no official warnings feed, so these alerts are
# derived from its daily forecast using common thresholds
# (roughly following US National Weather Service criteria).

def check_day_for_alerts(daily: dict, i: int) -> list[dict]:
    """Return the alerts triggered by one day of the daily forecast."""
    alerts = []

    def add(level: str, event: str, detail: str) -> None:
        alerts.append({"level": level, "event": event, "detail": detail})

    code = daily["weather_code"][i]
    rain_mm = daily["precipitation_sum"][i] or 0
    snow_cm = daily["snowfall_sum"][i] or 0
    gusts_mph = daily["wind_gusts_10m_max"][i] or 0
    feels_max_f = daily["apparent_temperature_max"][i]
    feels_min_f = daily["apparent_temperature_min"][i]
    uv = daily["uv_index_max"][i] or 0

    # Severe weather from the WMO weather code
    if code in (96, 99):
        add("warning", "Thunderstorm with hail", f"Weather code {code}")
    elif code == 95:
        add("warning", "Thunderstorm", "Weather code 95")
    if code in (56, 57, 66, 67):
        add("warning", "Freezing rain or drizzle", f"Weather code {code}")
    if code in (45, 48):
        add("advisory", "Freezing fog" if code == 48 else "Fog", f"Weather code {code}")

    # Rain
    if rain_mm >= 50:
        add("warning", "Heavy rain", f"{rain_mm} mm expected")
    elif rain_mm >= 25 or code in (65, 82):
        add("advisory", "Heavy rain", f"{rain_mm} mm expected")

    # Snow
    if snow_cm >= 15:
        add("warning", "Heavy snow", f"{snow_cm} cm expected")
    elif snow_cm >= 5:
        add("advisory", "Snow", f"{snow_cm} cm expected")

    # Wind
    if gusts_mph >= 58:
        add("warning", "High wind", f"Gusts up to {gusts_mph} mph")
    elif gusts_mph >= 45:
        add("advisory", "Wind", f"Gusts up to {gusts_mph} mph")

    # Heat and cold (using the "feels like" temperature)
    if feels_max_f is not None and feels_max_f >= 105:
        add("warning", "Extreme heat", f"Feels like up to {feels_max_f}°F")
    elif feels_max_f is not None and feels_max_f >= 100:
        add("advisory", "Heat", f"Feels like up to {feels_max_f}°F")
    if feels_min_f is not None and feels_min_f <= -15:
        add("warning", "Extreme cold", f"Feels like down to {feels_min_f}°F")
    elif feels_min_f is not None and feels_min_f <= 0:
        add("advisory", "Cold", f"Feels like down to {feels_min_f}°F")

    # UV
    if uv >= 11:
        add("warning", "Extreme UV", f"UV index {uv}")
    elif uv >= 8:
        add("advisory", "Very high UV", f"UV index {uv}")

    return alerts


def get_alerts_data(location: str, preferred_tz: str) -> dict:
    try:
        # Get coordinates
        coordinates = get_coordinates(location)

        if not coordinates:
            return {"error": f"City not found: {location}"}

        latitude = coordinates["latitude"]
        longitude = coordinates["longitude"]

        # Open-Meteo forecast API, asking only for the fields
        # the alert checks need
        response = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "timezone": "auto",
                "latitude": latitude,
                "longitude": longitude,
                "daily": ",".join([
                    "weather_code",
                    "precipitation_sum",
                    "snowfall_sum",
                    "wind_gusts_10m_max",
                    "apparent_temperature_max",
                    "apparent_temperature_min",
                    "uv_index_max",
                ]),
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "forecast_days": "3",
            },
            timeout=FETCH_TIMEOUT_S,
        )

        if response.status_code != 200:
            raise RuntimeError("Alerts API request failed")

        data = response.json()

        if not data.get("daily"):
            return {"error": "Forecast data for alerts unavailable"}

        daily = data["daily"]

        days = [
            {
                "date": date,
                "day_of_week": datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
                "alerts": check_day_for_alerts(daily, i),
            }
            for i, date in enumerate(daily["time"])
        ]

        return {
            "location": location,
            "latitude": latitude,
            "longitude": longitude,

            "city_timezone": data["timezone"],
            "preferred_timezone": preferred_tz,

            "source": "Derived from the Open-Meteo forecast; not official government warnings",
            "alert_count": sum(len(day["alerts"]) for day in days),
            "days": days,
        }

    except Exception as error:
        print("Alerts error:", error)
        return {"error": str(error) or "Unable to retrieve weather alerts"}


# --------------------------------------------------
# 7. Define Claude tools (schemas are built from the
#    type hints and docstrings by @beta_tool)
# --------------------------------------------------

@beta_tool
def get_weather(city: str) -> str:
    """Get today's actual current weather for a city.

    Args:
        city: The city to check
    """
    print(f"\nFetching current weather for {city}...")
    result = get_weather_data(city, preferred_time_zone)
    return json.dumps(result, indent=2)


@beta_tool
def get_forecast(city: str) -> str:
    """Get the weather forecast for the next three days for a city.

    Args:
        city: The city to check
    """
    print(f"\nFetching 3-day forecast for {city}...")
    result = get_forecast_data(city, preferred_time_zone)
    return json.dumps(result, indent=2)


@beta_tool
def get_time_of_day(city: str) -> str:
    """Get the actual current local time, date, timezone, and time of day (morning, afternoon, evening, or night) for any city. Also compare it with the user's preferred timezone.

    Args:
        city: The city to check the local time for
    """
    print(f"\nFetching local time for {city}...")
    result = get_time_of_day_data(city, preferred_time_zone)
    return json.dumps(result, indent=2)


@beta_tool
def get_weather_alerts(city: str) -> str:
    """Check the next three days for severe weather in a city (thunderstorms, hail, freezing rain, fog, heavy rain or snow, high wind, extreme heat or cold, very high UV). Alerts are derived from the forecast, not official government warnings.

    Args:
        city: The city to check for weather alerts
    """
    print(f"\nChecking weather alerts for {city}...")
    result = get_alerts_data(city, preferred_time_zone)
    return json.dumps(result, indent=2)


def build_system_prompt() -> str:
    # Standing instructions for Claude (sent as the system prompt
    # so they don't repeat in the conversation history)
    return f"""
You are a weather assistant.

Available tools:

1. get_weather:
   Retrieves actual current weather.

2. get_forecast:
   Retrieves the next three days of weather.

3. get_time_of_day:
   Retrieves the actual local time and date
   for a city.

4. get_weather_alerts:
   Checks the next three days for severe weather.

TIMEZONE INFORMATION:
- Server timezone: {server_time_zone}
- Preferred timezone: {preferred_time_zone}

TIMEZONE RULES:
- city_current_time is the actual current time in the
  requested city's timezone.
- preferred_current_time is the actual current time
  in the user's preferred timezone.
- Both timestamps represent the exact same instant.
- Never use weather_observation_time as the current clock time.
- weather_observation_time is only the timestamp
  associated with the weather observation.
- Never independently calculate or guess the time.
- Display the exact timestamps returned by the tools.

INSTRUCTIONS:

- If the user asks about weather, use get_weather.
- If the user asks about a forecast, use get_forecast.
- If the user asks about local time, use get_time_of_day.
- If the user asks about alerts, warnings, or severe weather,
  use get_weather_alerts.
- When you report alerts, say they are derived from the
  forecast and are not official warnings. Point the user to
  their local weather service for official warnings.
- If the user asks about both weather and time,
  use the appropriate tools.
- If the user asks for a time comparison,
  use get_time_of_day for the requested cities.
- If a follow-up question doesn't name a city, use the
  city from earlier in the conversation.
- Always use the timezone information returned
  by the tools.
- Never guess the current time or date.
- Never confuse weather observation time
  with the actual current time.
- Never invent weather information.

CLOTHING RECOMMENDATIONS:
- Recommend appropriate clothing for today.
- Identify rainy or unusually windy days.
- Recommend what to pack for the next three days.


Provide clear, conversational answers.
If a tool returns an error, explain it clearly.
Never invent weather information.
"""


# --------------------------------------------------
# 8. Interactive weather assistant
# --------------------------------------------------

def main() -> None:
    global preferred_time_zone

    print("======================================")
    print("       WEATHER AI ASSISTANT")
    print("======================================")
    print("Ask about current weather or forecasts.")
    print("Type 'quit' or 'exit' to stop.")
    print("======================================")

    timezone_input = input(
        f"\nYour server timezone is {server_time_zone}. "
        "Enter your preferred timezone (or press Enter to use this): "
    ).strip()

    if timezone_input:
        try:
            ZoneInfo(timezone_input)
            preferred_time_zone = timezone_input
        except (ZoneInfoNotFoundError, ValueError):
            print("Invalid timezone. Using server timezone.")

    print(f"Using timezone: {preferred_time_zone}")

    system_prompt = build_system_prompt()

    # Conversation history, kept across questions so follow-ups
    # like "what about tomorrow?" know which city was meant
    history: list[dict] = []

    # Interactive loop
    while True:
        # Ask user for a city
        try:
            location = input(
                "\nWhat would you like to know? "
                "(e.g. Weather in LA, forecast for NYC, or time in Tokyo): "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! Thanks for using Weather AI.")
            break

        # Exit condition
        if location.lower() in ("quit", "exit"):
            print("\nGoodbye! Thanks for using Weather AI.")
            break

        # Validate input
        if not location:
            print("Please enter a valid city name.")
            continue

        history.append({"role": "user", "content": location})

        try:
            # --------------------------------------------------
            # 9. Run Claude with automatic tool execution
            # --------------------------------------------------

            runner = client.beta.messages.tool_runner(
                model="claude-opus-5-5",
                # Thinking counts toward max_tokens, so leave plenty of room
                max_tokens=16000,
                # "summarized" returns a readable summary of Claude's reasoning
                # (the default, "omitted", returns empty thinking text)
                thinking={"type": "adaptive", "display": "summarized"},
                # low | medium | high | xhigh | max (Opus 5.5 defaults to medium)
                output_config={"effort": "medium"},
                # If a safety classifier declines the request, let the API
                # retry it on a fallback model instead of stopping
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=system_prompt,
                # Pass a copy so the runner can't modify our history
                messages=list(history),
                tools=[get_weather, get_forecast, get_time_of_day, get_weather_alerts],
            )

            # Step through each round of the conversation (Claude may call
            # tools several times), show its reasoning as it goes, and
            # record every round exactly as it was sent
            final_message = None
            turn: list = []
            for message in runner:
                for block in message.content:
                    if block.type == "thinking" and block.thinking:
                        print(f"\n[Thinking] {block.thinking}")
                final_message = message

                # Claude's message, unchanged (thinking and tool calls included)
                turn.append({"role": "assistant", "content": message.content})

                # The tool results the runner sends back next. The runner
                # caches them, so this doesn't run any tool twice.
                tool_results = runner.generate_tool_call_response()
                if tool_results is not None:
                    turn.append(tool_results)

            if final_message is None or final_message.stop_reason == "refusal":
                history.pop()
                print("\nClaude declined to answer that request.")
                continue

            # Keep the whole exchange for follow-up questions. Thinking
            # blocks are only valid alongside the exact conversation that
            # produced them, so the history is only ever appended to.
            history.extend(turn)

            # --------------------------------------------------
            # 10. Display Claude's final response
            # --------------------------------------------------

            print("\n======================================")
            print("         WEATHER ASSISTANT")
            print("======================================")

            for block in final_message.content:
                if block.type == "text":
                    print(block.text)

            print("\n======================================")

        except Exception as error:
            # Drop the unanswered question so the history stays valid
            history.pop()

            print("\nAn error occurred:", error)
            print("Please try again with another city.")


if __name__ == "__main__":
    main()
