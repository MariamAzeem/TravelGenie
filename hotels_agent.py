import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

def get_hotels(destination, budget, travelers, duration):
    """Generate plausible hotel options using Groq. These are estimates, not live inventory."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""
You are a travel hotel-planning agent.
Create 5 plausible hotel options in {destination}.
Travelers: {travelers}
Trip duration: {duration} days
Total user budget: PKR {budget}

Return ONLY valid JSON as a list of 5 objects. Each object must contain:
name, price_per_night, rating, location, amenities.
price_per_night is the estimated room price in PKR.
Do not include markdown.
These are planning estimates, not live hotel availability.
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    return json.loads(response.choices[0].message.content)
