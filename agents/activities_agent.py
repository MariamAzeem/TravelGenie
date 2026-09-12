import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
def get_activities(destination, interests, travelers, duration, budget):
    """
    Generates activities because the uploaded agent set does not currently
    contain a dedicated activities_agent.py file.
    """

    prompt = f"""
You are the activities agent for an AI travel planning application.

Destination: {destination}
Interests: {interests}
Travelers: {travelers}
Trip duration: {duration} days
Total group budget: {budget} PKR

Suggest 8 to 12 suitable activities or attractions. Include a mixture matching
the user's interests and practical travel experiences. Each estimated_cost must
be PER PERSON in PKR.

Return ONLY valid JSON in this exact format:
[
  {{
    "name": "Activity name",
    "estimated_cost": 0,
    "category": "sightseeing"
  }}
]
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=2500,
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
            return []

if __name__ == "__main__":
    result = get_activities(destination="Istanbul, Turkey", interests="history, food", travelers=2, duration=4, budget=200000)
    print(json.dumps(result, indent=2))
