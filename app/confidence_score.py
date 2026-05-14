# ==================== CONFIDENCE SCORE CALCULATION ====================

from utilities.property_utils import get_property_details

# ==================== FACTOR 1: QUERY TYPE BASE SCORE ====================
def get_query_type_base_score(query_type: str) -> float:
    """
    Base confidence score for each query type
    
    - pre_sales_availability/pre_sales_pricing: 0.90 (well-defined, property context has data)
    - post_sales_checkin: 0.85 (known info but post-booking, personal)
    - general_enquiry: 0.80 (answerable but scope can be vague)
    - special_request: 0.65 (needs human coordination)
    - complaint: 0.35 (always escalate to human)
    """
    base_scores = {
        "pre_sales_availability": 0.90,
        "pre_sales_pricing": 0.90,
        "post_sales_checkin": 0.85,
        "general_enquiry": 0.80,
        "special_request": 0.65,
        "complaint": 0.35,
    }
    return base_scores.get(query_type, 0.70)


# ==================== FACTOR 2: CONTEXT COVERAGE ====================
def check_context_coverage(query_type: str, message_text: str) -> float:
    """
    Check if query topic exists in property context
    
    +0.10: Query topic found in property context (e.g., "WiFi password" in context)
    -0.10: Query topic NOT in property context (e.g., asks about pet policy, we have no data)
    +0.00: Cannot determine or N/A
    """
    message_lower = message_text.lower()
    property_info = get_property_details()
    
    # Topics that ARE in property context
    context_keywords = [
        "wifi", "password", "check-in", "check in", "check-out", "check out",
        "bedrooms", "guests", "rate", "price", "pool", "caretaker", "chef",
        "cancellation", "availability", "dates", "booking"
    ]
    
    # Topics that are NOT in property context
    unknown_keywords = [
        "pet", "parking", "smoking", "children", "cot", "baby", "high chair",
        "wheelchair", "accessibility", "hot tub", "gym", "yoga"
    ]
    
    has_context_topic = any(kw in message_lower for kw in context_keywords)
    has_unknown_topic = any(kw in message_lower for kw in unknown_keywords)
    
    if has_unknown_topic and not has_context_topic:
        return -0.10  # Topic not in context
    elif has_context_topic:
        return +0.10  # Topic found in context
    else:
        return +0.00  # Cannot determine


# ==================== FACTOR 3: BOOKING REFERENCE ====================
def check_booking_reference(booking_ref: str) -> float:
    """
    Presence of booking reference indicates more grounded query
    
    +0.05: booking_ref present and valid
    +0.00: No booking_ref (pre-booking queries are still answerable)
    """
    if booking_ref and booking_ref != "N/A":
        return +0.05
    return +0.00


# ==================== FACTOR 4: MESSAGE CLARITY ====================
def assess_message_clarity(message_text: str) -> float:
    """
    Assess clarity of guest's question
    
    +0.05: Single, specific question (high clarity)
    +0.00: Multi-part but coherent (answerable but more complex)
    -0.10: Vague or ambiguous (unclear intent)
    """
    message_lower = message_text.lower()
    question_count = message_text.count("?")
    
    # Check for vague patterns
    vague_patterns = ["what can you do", "can you help", "what do you offer", "anything else"]
    is_vague = any(pattern in message_lower for pattern in vague_patterns)
    
    if is_vague:
        return -0.10
    elif question_count == 1:
        return +0.05  # Single question = clear intent
    elif question_count > 1:
        return +0.00  # Multiple questions but coherent
    else:
        return +0.00


# ==================== FACTOR 5: SENTIMENT PENALTY ====================
def analyze_sentiment(message_text: str) -> float:
    """
    Detect sentiment and apply penalty for negative sentiment
    
    -0.20: Strong negative sentiment (keywords: not happy, unacceptable, refund, broken, terrible, disgusting)
    -0.10: Mild concern/frustration (keywords: issue, problem, not working, confused, disappointed)
    +0.00: Neutral or positive (normal enquiry tone)
    """
    message_lower = message_text.lower()
    
    # Strong negative sentiment keywords
    strong_negative = [
        "not happy", "unacceptable", "refund", "broken", "terrible",
        "disgusting", "unhappy", "worst", "never again", "disappointed"
    ]
    
    # Mild concern/frustration keywords
    mild_negative = [
        "issue", "problem", "not working", "confused", "disappointed",
        "difficult", "complicated", "concerned", "worried"
    ]
    
    has_strong_negative = any(kw in message_lower for kw in strong_negative)
    has_mild_negative = any(kw in message_lower for kw in mild_negative)
    
    if has_strong_negative:
        return -0.20
    elif has_mild_negative:
        return -0.10
    else:
        return +0.00


# ==================== CALCULATE FINAL CONFIDENCE SCORE ====================
def calculate_confidence_score(
    query_type: str,
    message_text: str,
    booking_ref: str
) -> float:
    """
    Calculate final confidence score using all 5 factors
    
    Formula: Base + Context + Booking_ref + Clarity + Sentiment
    Clamped to [0, 1]
    
    Returns:
        float: Confidence score between 0 and 1
    """
    base_score = get_query_type_base_score(query_type)
    context_score = check_context_coverage(query_type, message_text)
    booking_score = check_booking_reference(booking_ref)
    clarity_score = assess_message_clarity(message_text)
    sentiment_score = analyze_sentiment(message_text)
    
    # Sum all factors
    total_score = base_score + context_score + booking_score + clarity_score + sentiment_score
    
    # Clamp to [0, 1]
    final_score = max(0.0, min(1.0, total_score))
    
    return round(final_score, 2)


# ==================== DETERMINE ACTION ====================
def determine_action(query_type: str, confidence_score: float) -> str:
    """
    Determine action based on confidence score and query type
    
    auto_send: >= 0.85 (send directly to guest)
    agent_review: 0.60-0.84 (show draft to agent before sending)
    escalate: < 0.60 or complaint query (route to human, AI draft suppressed)
    
    Args:
        query_type: Type of query
        confidence_score: Calculated confidence score
    
    Returns:
        str: Action to take (auto_send, agent_review, escalate)
    """
    # Always escalate complaints, regardless of confidence score
    if query_type == "complaint":
        return "escalate"
    
    # Threshold-based routing
    if confidence_score >= 0.85:
        return "auto_send"
    elif confidence_score >= 0.60:
        return "agent_review"
    else:
        return "escalate"
