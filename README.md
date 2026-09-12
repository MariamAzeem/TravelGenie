# TravelGenie

Modern Streamlit multi-agent AI travel planner.

Features:
- Modern travel-app dashboard
- Dark planning sidebar
- Hero landing section
- Trip summary cards
- Day-by-day itinerary timeline
- Budget progress dashboard
- Flight, hotel and experience cards
- Conditional weather forecast
- Plan-another-trip workflow

Weather is used only when the complete trip fits the available Open-Meteo forecast window. Otherwise the trip continues without fabricated weather information.

Setup:
1. `pip install -r requirements.txt`
2. Add `GROQ_API_KEY` to `.env` locally or Streamlit Secrets in the cloud.
3. Optional: `GROQ_MODEL=openai/gpt-oss-120b`
4. `streamlit run app.py`

Flights, hotels and activities are AI-generated planning estimates, not live booking inventory.
