import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

def get_activities(destination, budget, travelers, duration, interests=None):
    """Generate activity suggestions. estimated_cost is PER PERSON in PKR."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    interests_text = ", ".join(interests or []) or "general sightseeing, food, culture, and local experiences"
    prompt = f"""
You are a travel activities-planning agent.
Create 8 useful activities for {destination}.
Trip duration: {duration} days
Travelers: {travelers}
Total budget: PKR {budget}
Traveler interests: {interests_text}

Return ONLY valid JSON as a list of 8 objects. Each object must contain:
name, estimated_cost, category, duration, indoor_outdoor.
estimated_cost must be an estimated cost PER PERSON in PKR.
duration should be a simple string such as "2-3 hours".
Do not include markdown.
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    return json.loads(response.choices[0].message.content)
