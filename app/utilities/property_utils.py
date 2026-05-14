# ==================== PROPERTY UTILITIES ====================

def get_property_details():
    """
    Return property information for context
    Used by AI to draft replies with accurate property details
    """
    return {
        "property": "Villa B1, Assagao, North Goa",
        "bedrooms": 3,
        "max_guests": 6,
        "private_pool": True,
        "check_in": "2pm",
        "check_out": "11am",
        "base_rate": {
            "amount": 18000,
            "currency": "INR",
            "per_night": "up to 4 guests"
        },
        "extra_guest": {
            "amount": 2000,
            "currency": "INR",
            "per_night": True
        },
        "wifi_password": "Nistula@2024",
        "caretaker": {
            "available": True,
            "hours": "8am to 10pm"
        },
        "chef_on_call": {
            "available": True,
            "pre_booking_required": True
        },
        "availability": {
            "dates": "April 20-24",
            "status": "Available"
        },
        "cancellation": "Free up to 7 days before check-in"
    }

def get_context_keywords():
    return {
    "pool": True, "checkin": True, "checkout": True, "wifi": True,
    "rate": True, "price": True, "available": True, "availability": True,
    "guest": True, "bedroom": True, "caretaker": True, "chef": True,
    "cancellation": True, "extra": True,
    }