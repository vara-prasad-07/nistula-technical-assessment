# ==================== MESSAGE UTILITIES ====================

import uuid
from datetime import datetime

# ============ Normalize incoming message from any channel to unified schema ==========
def normalize_message(payload: dict) -> dict:
    """
    Args:
        payload: Raw message payload from webhook
    
    Returns:
        dict: Normalized message with UUID, timestamps, and standardized fields
    """
    normalized = {
        "message_id": str(uuid.uuid4()),
        "source": payload.get("source", "unknown"),
        "guest_name": payload.get("guest_name", "Guest"),
        "message_text": payload.get("message", ""),
        "timestamp": payload.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        "booking_ref": payload.get("booking_ref", "N/A"),
        "property_id": payload.get("property_id", "villa-b1"),
        "query_type": None  # Will be classified later
    }
    return normalized


def classify_query(message_text: str) -> str:
    """
    Classify the message into one of 6 query types using enhanced pattern matching:
    - pre_sales_availability: Is the villa available on these dates?
    - pre_sales_pricing: What is the rate for 2 adults 3 nights?
    - post_sales_checkin: What time can we check in? WiFi password?
    - special_request: Early check-in, airport transfer?
    - complaint: The AC is not working. I am not happy.
    - general_enquiry: Do you allow pets? Is there parking?
    
    Args:
        message_text: Guest message to classify
    
    Returns:
        str: Query type classification
    """
    message_lower = message_text.lower()
    
    # Enhanced keyword dictionaries with weighted scoring
    availability_keywords = {
        # Primary indicators
        "available": 3, "availability": 3, "dates": 2, "book": 2, "booking": 2,
        # Date-related
        "when": 1, "during": 1, "from": 1, "to": 1, "month": 1, "week": 1,
        # Confirmation patterns
        "is it available": 4, "can we book": 3, "can i book": 3
    }
    
    pricing_keywords = {
        # Primary indicators
        "price": 3, "pricing": 3, "rate": 3, "cost": 3, "charge": 2,
        # Amount queries
        "how much": 3, "per night": 2, "per day": 2, "discount": 2,
        # Variation patterns
        "expensive": 1, "affordable": 1, "quote": 2, "estimate": 2
    }
    
    checkin_keywords = {
        # Primary indicators
        "check-in": 4, "check in": 4, "checkin": 4, "arrival": 2,
        # Access & amenities
        "wifi": 3, "password": 3, "keys": 2, "access": 2, "entry": 2,
        # Timing
        "time": 1, "what time": 2, "when can": 1, "early check": 2
    }
    
    special_keywords = {
        # Primary indicators
        "early": 2, "late": 2, "checkout": 2, "check-out": 2,
        # Services
        "transfer": 3, "airport": 2, "pickup": 2, "request": 1, "special": 1,
        # Amenities
        "cooking": 1, "chef": 2, "meal": 1, "catering": 2
    }
    
    complaint_keywords = {
        # Primary indicators
        "broken": 3, "not working": 3, "problem": 3, "issue": 3, "complaint": 4,
        # Sentiment markers
        "unhappy": 3, "disappointed": 3, "frustrated": 3, "not satisfied": 3,
        # Damage/malfunction
        "broken": 3, "damage": 2, "leak": 2, "noise": 1, "dirty": 2, "missing": 1
    }
    
    general_keywords = {
        # Facilities
        "pool": 1, "parking": 1, "kitchen": 1, "laundry": 1,
        # Policies
        "pets": 2, "children": 1, "babies": 1, "smoking": 1, "refund": 1
    }
    
    # Calculate weighted scores
    scores = {
        "pre_sales_availability": _calculate_score(message_lower, availability_keywords),
        "pre_sales_pricing": _calculate_score(message_lower, pricing_keywords),
        "post_sales_checkin": _calculate_score(message_lower, checkin_keywords),
        "special_request": _calculate_score(message_lower, special_keywords),
        "complaint": _calculate_score(message_lower, complaint_keywords),
        "general_enquiry": _calculate_score(message_lower, general_keywords),
    }
    
    # Get highest score
    max_score = max(scores.values())
    
    # If all scores are 0, default to general enquiry
    if max_score == 0:
        return "general_enquiry"
    
    # Return the category with highest score
    best_match = max(scores, key=scores.get)
    return best_match


def _calculate_score(message_lower: str, keywords_dict: dict) -> int:
    """
    Calculate weighted score for keyword matches in message.
    Handles phrase matching and prevents double-counting.
    
    Args:
        message_lower: Lowercase message text
        keywords_dict: Dictionary of keywords with weights
    
    Returns:
        int: Total weighted score
    """
    score = 0
    counted_positions = set()
    
    # Sort by length (longest first) to match phrases before individual words
    sorted_keywords = sorted(keywords_dict.keys(), key=len, reverse=True)
    
    for keyword in sorted_keywords:
        weight = keywords_dict[keyword]
        start = 0
        while True:
            pos = message_lower.find(keyword, start)
            if pos == -1:
                break
            # Check if this position overlaps with already counted keywords
            keyword_range = set(range(pos, pos + len(keyword)))
            if not keyword_range.intersection(counted_positions):
                score += weight
                counted_positions.update(keyword_range)
            start = pos + 1
    
    return score
