from datetime import date, timedelta
import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MAX_FORECAST_DAYS = 16

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

def _geocode(destination):
    destination = (destination or "").strip()
    if not destination:
        raise ValueError("Destination cannot be empty.")

    queries = [destination]
    if "," in destination:
        city_only = destination.split(",")[0].strip()
        if city_only and city_only.lower() != destination.lower():
            queries.append(city_only)

    last_error = None
    for query in queries:
        try:
            response = requests.get(
                GEOCODING_URL,
                params={
                    "name": query,
                    "count": 10,
                    "language": "en",
                    "format": "json",
                },
                timeout=15,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                continue

            preferred_codes = {"PPLC", "PPLA", "PPLA2", "PPLA3", "PPLA4"}
            preferred = [r for r in results if r.get("feature_code") in preferred_codes]
            result = preferred[0] if preferred else results[0]
            return {
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "name": result.get("name", query),
                "country": result.get("country", ""),
            }
        except requests.RequestException as exc:
            last_error = exc

    detail = f" ({last_error})" if last_error else ""
    raise ValueError(f"Could not find a location for '{destination}'.{detail}")

def get_weather(destination, duration, start_date=None):
    """
    Return weather only when the whole requested trip fits inside Open-Meteo's
    available forecast window. Otherwise return a structured unavailable result.

    Open-Meteo supports forecast data up to 16 days ahead. We use a conservative
    16-day window and do not fabricate long-range weather.
    """
    start = start_date or date.today()
    if isinstance(start, str):
        start = date.fromisoformat(start)

    duration = max(1, int(duration))
    end = start + timedelta(days=duration - 1)
    today = date.today()
    latest_forecast_date = today + timedelta(days=MAX_FORECAST_DAYS - 1)

    if start < today or start > latest_forecast_date or end > latest_forecast_date:
        return {
            "available": False,
            "reason": (
                f"Weather forecast is available only for trips fully within "
                f"{today.isoformat()} to {latest_forecast_date.isoformat()}."
            ),
            "forecast": [],
        }

    location = _geocode(destination)

    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "daily": ",".join([
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
            ]),
            "timezone": "auto",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    daily = data.get("daily", {})
    result = []
    for i, day in enumerate(daily.get("time", [])):
        code = daily.get("weather_code", [None] * len(result))[i]
        result.append({
            "date": day,
            "condition": WEATHER_CODES.get(code, "Unknown"),
            "temp_max_c": daily.get("temperature_2m_max", [None] * len(result))[i],
            "temp_min_c": daily.get("temperature_2m_min", [None] * len(result))[i],
            "precipitation_probability": daily.get(
                "precipitation_probability_max", [None] * len(result)
            )[i],
        })

    return {
        "available": True,
        "reason": None,
        "forecast": result,
        "location": location,
    }
