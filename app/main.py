from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from claude_service import ClaudeService
from utilities.message_utils import normalize_message, classify_query

app = FastAPI()

# ==================== CORS CONFIGURATION ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

claude_service = ClaudeService()

# ==================== DATA MODELS ====================
class InboundMessage(BaseModel):
    """Webhook payload schema for inbound guest messages"""
    source: str 
    guest_name: str
    message: str
    timestamp: str
    booking_ref: str
    property_id: str

class DraftedReplyResponse(BaseModel):
    """Response schema for drafted reply"""
    message_id: str
    query_type: str
    drafted_reply: str
    confidence_score: float
    action: str

# ==================== WEBHOOK ENDPOINT ====================
@app.post("/webhook/message", response_model=DraftedReplyResponse)
async def receive_guest_message(payload: InboundMessage):
    """
    Main webhook endpoint for receiving guest messages from multiple channels.
    
    Flow:
    1. Validate and normalize message to unified schema
    2. Classify query type
    3. Generate AI-drafted reply with property context
    4. Return drafted reply with confidence score
    
    Args:
        payload: InboundMessage from any channel (WhatsApp, Booking.com, etc.)
    
    Returns:
        DraftedReplyResponse: Drafted reply with confidence score
    """
    try:
        # Validate message field is not empty
        if not payload.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Invalid request: message field is empty"
            )
        
        # Step 1: Normalize message to unified schema
        normalized_message = normalize_message(payload.dict())
        
        # Step 2: Classify query type
        query_type = classify_query(normalized_message["message_text"])
        normalized_message["query_type"] = query_type
        
        # Step 3: Generate AI-drafted reply
        response = await claude_service.generate_reply(normalized_message)
        
        # Step 4: Return response
        return DraftedReplyResponse(
            message_id=response["message_id"],
            query_type=response["query_type"],
            drafted_reply=response["drafted_reply"],
            confidence_score=response["confidence_score"],
            action=response["action"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

# ==================== HEALTH CHECK ====================
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}