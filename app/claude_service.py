from anthropic import AsyncAnthropic
import os
from dotenv import load_dotenv
from utilities.property_utils import get_property_details
from confidence_score import calculate_confidence_score, determine_action

load_dotenv()

calude_client = AsyncAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY", "").strip()
)

class ClaudeService:
    def __init__(self):
        self.calude_client = calude_client
    
    # ==================== AI REPLY GENERATION ====================
    async def generate_reply(self, normalized_message: dict) -> dict:
        """
        Generate AI-drafted reply using Claude with property context
        and calculate confidence score + determine action
        
        Input: Normalized message with query classification
        Output: Dictionary with drafted_reply, confidence_score, and action
        
        Process:
        1. Retrieve property context
        2. Build system prompt with property details and query type
        3. Call Claude API to generate professional reply
        4. Calculate confidence score based on 5 factors
        5. Determine action (auto_send, agent_review, escalate)
        """
        query_type = normalized_message.get("query_type")
        message_text = normalized_message.get("message_text")
        guest_name = normalized_message.get("guest_name")
        booking_ref = normalized_message.get("booking_ref", "N/A")
        property_info = get_property_details()
        
        # Build system context with property details
        system_context = f"""You are a helpful property manager assistant for Nistula Villa B1.
        
        Property Details:
        - {property_info['property']}
        - Bedrooms: {property_info['bedrooms']}, Max Guests: {property_info['max_guests']}
        - Check-in: {property_info['check_in']}, Check-out: {property_info['check_out']}
        - Base Rate: ₹{property_info['base_rate']['amount']}/night (up to 4 guests)
        - Extra Guest: ₹{property_info['extra_guest']['amount']}/night
        - WiFi: {property_info['wifi_password']}
        - Caretaker: Available {property_info['caretaker']['hours']}
        - Chef on Call: {property_info['chef_on_call']['available']} (pre-booking required)
        - Cancellation: {property_info['cancellation']}

        Query Type: {query_type}
        Guest Name: {guest_name}

        Draft a professional, warm, and helpful reply. Keep it concise (2-3 sentences max). Be specific using the property details above."""

        # Call LLM service to generate draft reply
        drafted_reply =  await self.claude_llm(system_context, message_text)
        
        # Calculate confidence score using all 5 factors
        confidence_score = calculate_confidence_score(
            query_type=query_type,
            message_text=message_text,
            booking_ref=booking_ref
        )
        
        # Determine action based on confidence score
        action = determine_action(query_type, confidence_score)
        
        return {
            "message_id": normalized_message.get("message_id"),
            "query_type": query_type,
            "drafted_reply": drafted_reply,
            "confidence_score": confidence_score,
            "action": action
        }
    
    async def claude_llm(self,system_context,message_text):
        response = await self.calude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            system=system_context,
            messages=[
                {
                    "role": "user",
                    "content": message_text
                }
            ]
        )
        return response.content[0].text
    
