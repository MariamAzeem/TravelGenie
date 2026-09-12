import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

def get_flights(origin, destination, budget, travelers, duration):
    """Generate plausible flight options using Groq. These are estimates, not live inventory."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""
You are a travel flight-planning agent.
Create 5 plausible flight options for a trip from {origin} to {destination}.
Travelers: {travelers}
Trip duration: {duration} days
Total user budget: PKR {budget}

Return ONLY valid JSON as a list of 5 objects. Each object must contain:
airline, price, departure_time, arrival_time, from, to.
price must be the estimated one-way price PER PERSON in PKR.
Do not include markdown.
These are planning estimates, not live prices.
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    content = response.choices[0].message.content
    return json.loads(content)
