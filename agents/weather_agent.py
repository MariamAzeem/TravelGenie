import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
def get_weather(destination, duration):
    """
    Creates weather context for the itinerary agent. The current uploaded
    agents do not include a live weather provider/API integration.
    """

    prompt = f"""
You are a travel weather planning assistant.

Destination: {destination}
Trip duration: {duration} days.

Create a planning-oriented weather forecast for {duration} days. If live weather
is unavailable, clearly use reasonable estimated seasonal conditions.

Return ONLY valid JSON:
[
  {{
    "date": "Day 1",
    "condition": "Sunny",
    "temp_high": 28,
    "temp_low": 18
  }}
]
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except Exception:
        start = raw.find("[")
        end = raw.rfind("]") + 1
        try:
            return json.loads(raw[start:end])
        except Exception:
            return [
                {
                    "date": f"Day {i}",
                    "condition": "Weather information unavailable",
                    "temp_high": 0,
                    "temp_low": 0,
                }
                for i in range(1, duration + 1)
            ]
if __name__ == "__main__":
    result = get_weather(destination="Istanbul, Turkey", duration=4)
    print(json.dumps(result, indent=2))
