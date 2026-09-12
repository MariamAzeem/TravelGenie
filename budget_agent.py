def _num(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)

def calculate_budget(flights, hotels, activities, user_budget, travelers, duration):
    travelers = int(travelers)
    duration = int(duration)
    user_budget = _num(user_budget)

    flight = min(flights, key=lambda x: _num(x.get("price")))
    hotel = min(hotels, key=lambda x: _num(x.get("price_per_night")))

    rooms_needed = max(1, (travelers + 1) // 2)
    flight_cost = _num(flight.get("price")) * travelers
    hotel_cost = _num(hotel.get("price_per_night")) * rooms_needed * max(duration - 1, 1)

    ranked_activities = sorted(
        activities,
        key=lambda x: _num(x.get("estimated_cost"))
    )
    chosen_activities = ranked_activities[:min(len(ranked_activities), max(duration, 1))]
    activity_cost = sum(_num(a.get("estimated_cost")) for a in chosen_activities) * travelers

    total = flight_cost + hotel_cost + activity_cost
    within_budget = total <= user_budget

    return {
        "chosen_flight": flight,
        "chosen_hotel": hotel,
        "rooms_needed": rooms_needed,
        "chosen_activities": chosen_activities,
        "total_estimated_cost": round(total, 2),
        "user_budget": user_budget,
        "within_budget": within_budget,
        "breakdown": {
            "flights": round(flight_cost, 2),
            "hotel": round(hotel_cost, 2),
            "activities": round(activity_cost, 2),
        },
        "suggestions": (
            "Plan is within budget."
            if within_budget
            else "Consider a cheaper flight, hotel, or fewer paid activities."
        ),
    }
