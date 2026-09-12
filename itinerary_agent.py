import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

def build_itinerary(budget_summary, weather_data, duration):
    """
    Build a day-by-day itinerary. Weather is optional: if unavailable,
    the itinerary is still generated without weather-specific claims.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    weather_available = bool(weather_data and weather_data.get("available"))
    weather_forecast = weather_data.get("forecast", []) if weather_data else []

    prompt = f"""
You are an AI travel itinerary agent.

Create a practical {duration}-day itinerary using the selected flight, hotel,
and activities below.

SELECTED FLIGHT:
{json.dumps(budget_summary.get("chosen_flight", {}), ensure_ascii=False)}

SELECTED HOTEL:
{json.dumps(budget_summary.get("chosen_hotel", {}), ensure_ascii=False)}

SELECTED ACTIVITIES:
{json.dumps(budget_summary.get("chosen_activities", []), ensure_ascii=False)}

WEATHER AVAILABLE: {weather_available}
WEATHER DATA:
{json.dumps(weather_forecast, ensure_ascii=False)}

Rules:
- Return ONLY valid JSON as a list with exactly {duration} day objects.
- Each object must contain: day, title, activities, notes.
- activities must be a list of strings.
- If weather is available, use it only when it helps schedule outdoor activities.
- If weather is not available, do NOT invent temperatures, rain, or weather conditions.
- Keep the plan realistic and balanced.
- Do not include markdown.
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    return json.loads(response.choices[0].message.content)
