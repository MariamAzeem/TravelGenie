import os
import time
import json
import streamlit as st
from groq import Groq

from flights_agent import get_flights
from hotels_agent import get_hotels
from budget_agent import calculate_budget
from itinerary_agent import build_itinerary


# ============================================================
# TravelGenie - Main Streamlit Application
# ============================================================

st.set_page_config(
    page_title="TravelGenie ✈️",
    page_icon="🧞‍♂️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -------------------- Custom Styling --------------------
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top left, #e8f5ff 0%, #f7fbff 45%, #ffffff 100%);
    }

    .hero-title {
        text-align: center;
        font-size: clamp(2.8rem, 7vw, 5.5rem);
        font-weight: 800;
        margin-bottom: 0;
        letter-spacing: -2px;
    }

    .gradient-text {
        background: linear-gradient(90deg, #2563eb, #7c3aed, #db2777);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .tagline {
        text-align: center;
        font-size: 1.25rem;
        color: #64748b;
        animation: fadeIn 2.2s ease-in forwards;
        opacity: 0;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .glass-card {
        background: rgba(255,255,255,0.86);
        border: 1px solid rgba(148,163,184,0.20);
        padding: 1.4rem;
        border-radius: 22px;
        box-shadow: 0 10px 30px rgba(15,23,42,0.08);
        margin-bottom: 1rem;
    }

    .metric-card {
        background: white;
        border-radius: 18px;
        padding: 1rem;
        border: 1px solid #e2e8f0;
        text-align: center;
    }

    .day-card {
        background: white;
        border-left: 5px solid #7c3aed;
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 4px 15px rgba(15,23,42,0.06);
    }

    .activity {
        background: #f8fafc;
        border-radius: 10px;
        padding: 0.65rem 0.8rem;
        margin: 0.45rem 0;
    }

    div.stButton > button {
        width: 100%;
        border: 0;
        border-radius: 14px;
        padding: 0.75rem;
        font-size: 1.05rem;
        font-weight: 700;
        color: white;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
    }
</style>
""", unsafe_allow_html=True)


# -------------------- Session State --------------------
defaults = {
    "show_splash": True,
    "splash_start": time.time(),
    "page": "input",
    "trip_result": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -------------------- API Key --------------------
def get_groq_api_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.getenv("GROQ_API_KEY")


def validate_api_key():
    api_key = get_groq_api_key()
    if not api_key:
        st.error(
            "GROQ_API_KEY is missing. Add it to Streamlit Secrets or your .env file."
        )
        st.stop()
    return api_key


# -------------------- Helpers --------------------
def clean_json_list(value):
    return value if isinstance(value, list) else []


def get_activities(destination, interests, travelers, duration, budget):
    """
    Generates activities because the uploaded agent set does not currently
    contain a dedicated activities_agent.py file.
    """
    api_key = validate_api_key()
    client = Groq(api_key=api_key)

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


def get_weather(destination, duration):
    """
    Creates weather context for the itinerary agent. The current uploaded
    agents do not include a live weather provider/API integration.
    """
    api_key = validate_api_key()
    client = Groq(api_key=api_key)

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


def run_trip_pipeline(origin, destination, budget, duration, travelers, interests):
    """Runs the multi-agent TravelGenie pipeline."""

    validate_api_key()

    progress = st.progress(0, text="TravelGenie is waking up its agents...")

    progress.progress(10, text="✈️ Flights agent is searching options...")
    flights = get_flights(
        origin=origin,
        destination=destination,
        budget=budget,
        travelers=travelers,
        duration=duration,
    )

    progress.progress(30, text="🏨 Hotels agent is finding stays...")
    hotels = get_hotels(
        destination=destination,
        budget=budget,
        travelers=travelers,
        duration=duration,
    )

    progress.progress(50, text="🎯 Activities agent is matching your interests...")
    activities = get_activities(
        destination=destination,
        interests=interests,
        travelers=travelers,
        duration=duration,
        budget=budget,
    )

    progress.progress(70, text="💰 Budget agent is optimizing your trip...")
    budget_summary = calculate_budget(
        flights=clean_json_list(flights),
        hotels=clean_json_list(hotels),
        activities=clean_json_list(activities),
        user_budget=budget,
        travelers=travelers,
        duration=duration,
    )

    progress.progress(85, text="🌤️ Preparing weather context...")
    weather = get_weather(destination, duration)

    progress.progress(95, text="🗓️ Itinerary agent is creating your journey...")
    itinerary = build_itinerary(
        budget_summary=budget_summary,
        weather=weather,
        duration=duration,
    )

    progress.progress(100, text="✨ Your personalized trip is ready!")
    time.sleep(0.5)
    progress.empty()

    return {
        "origin": origin,
        "destination": destination,
        "budget": budget,
        "duration": duration,
        "travelers": travelers,
        "interests": interests,
        "flights": flights,
        "hotels": hotels,
        "activities": activities,
        "budget_summary": budget_summary,
        "weather": weather,
        "itinerary": itinerary,
    }


# -------------------- Splash Screen --------------------
if st.session_state.show_splash:
    elapsed = time.time() - st.session_state.splash_start

    if elapsed < 3:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="hero-title">🧞‍♂️ <span class="gradient-text">TravelGenie</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="tagline">Tell us where you dream of going. '
            'Your AI Genie plans the journey. ✨</div>',
            unsafe_allow_html=True,
        )
        time.sleep(max(0, 3 - elapsed))
        st.session_state.show_splash = False
        st.rerun()
    else:
        st.session_state.show_splash = False
        st.rerun()


# -------------------- Input Screen --------------------
if st.session_state.page == "input":
    st.markdown(
        '<div class="hero-title">🧞‍♂️ <span class="gradient-text">TravelGenie</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="tagline">Your personal AI travel expert — from dream to day-by-day plan.</div><br>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Plan your next adventure ✈️")

    with st.form("trip_form"):
        col1, col2 = st.columns(2)

        with col1:
            origin = st.text_input(
                "📍 Traveling from",
                placeholder="e.g. Islamabad, Pakistan",
            )
            destination = st.text_input(
                "🌍 Destination",
                placeholder="e.g. Istanbul, Turkey",
            )
            budget = st.number_input(
                "💰 Total budget (PKR)",
                min_value=1_000,
                value=150_000,
                step=5_000,
            )

        with col2:
            duration = st.number_input(
                "📅 Duration (days)",
                min_value=1,
                max_value=30,
                value=5,
                step=1,
            )
            travelers = st.number_input(
                "👥 Number of travelers",
                min_value=1,
                max_value=20,
                value=2,
                step=1,
            )
            interests = st.text_input(
                "❤️ Interests",
                placeholder="e.g. history, food, nature, shopping",
            )

        submitted = st.form_submit_button("✨ Generate My Trip")

    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        if not origin.strip() or not destination.strip() or not interests.strip():
            st.warning("Please complete origin, destination, and interests.")
        else:
            try:
                result = run_trip_pipeline(
                    origin=origin.strip(),
                    destination=destination.strip(),
                    budget=float(budget),
                    duration=int(duration),
                    travelers=int(travelers),
                    interests=interests.strip(),
                )

                st.session_state.trip_result = result
                st.session_state.page = "output"
                st.rerun()

            except Exception as exc:
                st.error("TravelGenie could not complete the trip planning pipeline.")
                st.exception(exc)


# -------------------- Output Screen --------------------
if st.session_state.page == "output" and st.session_state.trip_result:
    result = st.session_state.trip_result
    budget_summary = result.get("budget_summary", {})
    itinerary = result.get("itinerary", [])

    top_left, top_right = st.columns([5, 1])

    with top_left:
        st.title(f"🧞‍♂️ Your {result['destination']} Adventure")
        st.caption(
            f"From {result['origin']} • {result['duration']} days • "
            f"{result['travelers']} traveler(s) • Interests: {result['interests']}"
        )

    with top_right:
        if st.button("🔄 New Trip"):
            st.session_state.page = "input"
            st.session_state.trip_result = None
            st.rerun()

    st.divider()

    # Summary metrics
    breakdown = budget_summary.get("breakdown", {})
    total_cost = budget_summary.get("total_estimated_cost", 0)
    within_budget = budget_summary.get("within_budget", False)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Estimated Cost", f"PKR {total_cost:,.0f}")
    c2.metric("🎯 Your Budget", f"PKR {result['budget']:,.0f}")
    c3.metric(
        "📊 Budget Status",
        "Within Budget" if within_budget else "Over Budget",
    )
    c4.metric("🗓️ Trip Length", f"{result['duration']} Days")

    st.markdown("<br>", unsafe_allow_html=True)

    # Selected flight and hotel
    info1, info2 = st.columns(2)

    with info1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("✈️ Selected Flight")
        flight = budget_summary.get("chosen_flight")
        if flight:
            st.write(f"**Airline:** {flight.get('airline', 'N/A')}")
            st.write(f"**Route:** {flight.get('from', result['origin'])} → {flight.get('to', result['destination'])}")
            st.write(f"**Departure:** {flight.get('departure_time', 'N/A')}")
            st.write(f"**Arrival:** {flight.get('arrival_time', 'N/A')}")
            st.write(f"**Price per person:** PKR {float(flight.get('price', 0)):,.0f}")
        else:
            st.info("No flight could be selected.")
        st.markdown("</div>", unsafe_allow_html=True)

    with info2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🏨 Selected Hotel")
        hotel = budget_summary.get("chosen_hotel")
        if hotel:
            st.write(f"**Hotel:** {hotel.get('name', 'N/A')}")
            st.write(f"**Location:** {hotel.get('location', 'N/A')}")
            st.write(f"**Rating:** ⭐ {hotel.get('rating', 'N/A')}")
            st.write(f"**Price per night:** PKR {float(hotel.get('price_per_night', 0)):,.0f}")
            st.write(f"**Rooms needed:** {budget_summary.get('rooms_needed', 'N/A')}")
        else:
            st.info("No hotel could be selected.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Budget breakdown
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("💰 Budget Breakdown")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Flights", f"PKR {float(breakdown.get('flights', 0)):,.0f}")
    b2.metric("Hotels", f"PKR {float(breakdown.get('hotels', 0)):,.0f}")
    b3.metric("Activities", f"PKR {float(breakdown.get('activities', 0)):,.0f}")
    b4.metric("Food & Misc.", f"PKR {float(breakdown.get('misc', 0)):,.0f}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Suggestions
    suggestions = budget_summary.get("suggestions", [])
    if suggestions:
        with st.expander("💡 TravelGenie's Budget Suggestions", expanded=True):
            for suggestion in suggestions:
                st.write(f"• {suggestion}")

    # Day-by-day itinerary
    st.subheader("🗓️ Your Day-by-Day Itinerary")

    if not isinstance(itinerary, list):
        itinerary = []

    for day_plan in itinerary:
        day_no = day_plan.get("day", "?")
        date = day_plan.get("date", f"Day {day_no}")
        weather = day_plan.get("weather", "Weather unavailable")
        day_cost = day_plan.get("estimated_day_cost", 0)

        with st.expander(
            f"Day {day_no} — {date}   |   🌤️ {weather}   |   PKR {float(day_cost):,.0f}",
            expanded=(day_no == 1),
        ):
            flight = day_plan.get("flight")
            if flight:
                st.info(
                    f"✈️ **Flight:** {flight.get('airline', 'N/A')} — "
                    f"{flight.get('departure_time', 'N/A')} to "
                    f"{flight.get('arrival_time', 'N/A')}"
                )

            hotel = day_plan.get("hotel")
            if hotel:
                st.success(f"🏨 **Stay:** {hotel.get('name', 'N/A')}")

            activities = day_plan.get("activities", [])
            if activities:
                st.markdown("**Today's plan:**")
                for activity in activities:
                    st.markdown(
                        f'<div class="activity">🕒 <b>{activity.get("time", "Flexible")}</b>'
                        f' — {activity.get("activity", "Activity")} '
                        f'• PKR {float(activity.get("cost", 0)):,.0f}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.write("A flexible day for travel, rest, and exploration.")

    # Technical/debug data hidden behind expanders
    with st.expander("🔍 View Agent Results"):
        st.json({
            "flights": result.get("flights", []),
            "hotels": result.get("hotels", []),
            "activities": result.get("activities", []),
            "weather": result.get("weather", []),
        })

    # Download itinerary
    downloadable = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    st.download_button(
        "📥 Download Trip Plan (JSON)",
        data=downloadable,
        file_name="travelgenie_trip_plan.json",
        mime="application/json",
    )
