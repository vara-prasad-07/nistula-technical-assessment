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
    Classify the message into one of 6 query types:
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
    
    # Keywords for each query type
    availability_keywords = ["available", "dates", "book", "when", "from", "to"]
    pricing_keywords = ["price", "rate", "cost", "how much", "charge", "per night"]
    checkin_keywords = ["check-in", "check in", "time", "wifi", "password", "access"]
    special_keywords = ["early", "late", "transfer", "airport", "request", "special"]
    complaint_keywords = ["broken", "not working", "complaint", "problem", "issue", "unhappy"]
    
    # Score each category
    scores = {
        "pre_sales_availability": sum(1 for kw in availability_keywords if kw in message_lower),
        "pre_sales_pricing": sum(1 for kw in pricing_keywords if kw in message_lower),
        "post_sales_checkin": sum(1 for kw in checkin_keywords if kw in message_lower),
        "special_request": sum(1 for kw in special_keywords if kw in message_lower),
        "complaint": sum(1 for kw in complaint_keywords if kw in message_lower),
    }
    
    # Return highest scoring category, default to general_enquiry
    best_match = max(scores, key=scores.get) if max(scores.values()) > 0 else "general_enquiry"
    return best_match
