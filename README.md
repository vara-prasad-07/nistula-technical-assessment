# Nistula Unified Messaging Platform

## Overview

Nistula is an intelligent guest messaging platform built for property managers. It receives messages from multiple channels—WhatsApp, Booking.com, Airbnb, Instagram, and direct inquiries—and automatically generates professional replies using AI. Every message is analyzed to determine whether it can be safely sent automatically, needs agent review, or requires human escalation.

The core innovation is a confidence scoring system that evaluates both the quality of the guest's question and the sentiment behind it. A clear availability question from a satisfied guest scores high and is auto-sent. A vague complaint scores low and gets routed to a human agent. This hybrid approach—AI speed with human oversight—delivers fast response times while maintaining service quality.

## Architecture

The system is built with:
- **FastAPI** - High-performance Python web framework for the webhook endpoints
- **Claude** - AI models for generating professional responses
- **PostgreSQL** - Database schema for guest profiles, conversations, and audit trails
- **Python** - Async processing for real-time message handling

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- PostgreSQL 12+ (optional, for database integration)
- API keys from Anthropic (Claude)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/vara-prasad-07/nistula-technical-assessment.git
cd nistula/app
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with your API keys:
```bash
ANTHROPIC_API_KEY=your_anthropic_key_here
```

5. Run the FastAPI application:
```bash
uvicorn main:app --reload
```

The application will start at `http://127.0.0.1:8000`

### Verify Installation

Access the interactive API documentation at:
```
http://127.0.0.1:8000/docs
```

Health check endpoint:
```
GET http://127.0.0.1:8000/health
```

## Testing Instructions

### Option 1: Interactive Testing via Swagger UI

1. Open your browser and navigate to: `http://127.0.0.1:8000/docs`

2. Find the `/webhook/message` endpoint in the list

3. Click "Try it out"

4. In the request body, paste the sample payload:
```json
{
  "source": "whatsapp",
  "guest_name": "Rahul Sharma",
  "message": "Is the villa available from April 20 to 24? What is the rate for 2 adults?",
  "timestamp": "2026-05-05T10:30:00Z",
  "booking_ref": "NIS-2024-0891",
  "property_id": "villa-b1"
}
```

5. Click "Execute" and view the response

You should receive a response like:
```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "query_type": "pre_sales_availability",
  "drafted_reply": "Hi Rahul! Great news—Villa B1 is available April 20-24. For 2 adults, the rate is ₹18,000 per night.",
  "confidence_score": 0.91,
  "action": "auto_send"
}
```

### Option 2: cURL / Postman Testing

Coming soon.

## Understanding Confidence Scores

### What Is Confidence?

Confidence measures how well the AI can answer a guest's question. A high score (0.85+) means the answer is reliable and can be sent directly to the guest. A low score (<0.60) means a human should review it first.

The score combines five independent factors: the type of question, whether we have the information, guest context, clarity of the question, and the guest's emotional tone.

### The Five Factors Explained

**Factor 1: Query Type Base Score**

The system recognizes six types of guest queries, each with different reliability:

- **0.90** — Availability or pricing questions (e.g., "Is the villa free April 20-24?"). These are straightforward. The property data contains dates and rates. High confidence.
- **0.85** — Check-in information requests (e.g., "What's the WiFi password?"). We have this data. Slightly lower because these are post-booking and personal.
- **0.80** — General inquiries (e.g., "Do you allow guests with dogs?"). Usually answerable but harder to scope.
- **0.65** — Special requests (e.g., "Can you arrange an airport transfer?"). These require human coordination and cannot be auto-confirmed.
- **0.35** — Complaints (e.g., "The AC is broken"). Always escalated to a human. AI replies to complaints often make things worse.

**Factor 2: Context Coverage**

Does the property information answer the guest's question?

- **+0.10** — The question asks about something in our database (WiFi, check-in time, cancellation policy). Confidence increases because the answer is factual.
- **-0.10** — The guest asks about something we don't track (pet policy, smoking areas, high chairs). The AI would be guessing, so confidence drops.
- **+0.00** — Cannot determine; no change.

**Factor 3: Booking Reference**

- **+0.05** — Guest provides their booking reference (e.g., "NIS-2024-0891"). More context about the guest leads to a more grounded, relevant reply.
- **+0.00** — No booking reference. Pre-booking inquiries are still answerable; no adjustment.

**Factor 4: Message Clarity**

How clear is the guest's intent?

- **+0.05** — Single, specific question (e.g., "What is the WiFi password?"). One clear intent, easy to answer completely.
- **+0.00** — Multi-part but coherent (e.g., "Available April 20-24? Rate for 2 adults?"). More complex but still answerable.
- **-0.10** — Vague or ambiguous (e.g., "What can you do for me?"). No clear intent to address.

**Factor 5: Sentiment Penalty**

How is the guest feeling?

- **-0.20** — Strong negative sentiment. Keywords like "not happy", "unacceptable", "broken", "terrible", "disgusting". A frustrated guest needs human empathy, not an automated reply.
- **-0.10** — Mild concern (e.g., "This is a problem", "I'm confused"). Still human territory.
- **+0.00** — Neutral or positive tone. Normal inquiry, no penalty.

### How the Calculation Works

The system sums all five factors and clamps the result between 0.0 and 1.0:

**Example 1: Strong Pre-Sales Query**
```
Query type base:     +0.90
Context (found):     +0.10
Booking reference:   +0.05
Clarity (specific):  +0.05
Sentiment (neutral): +0.00
─────────────────────────
Total:                1.10  → clamped to 1.00
```
Result: **Confidence 1.00** → **auto_send**

**Example 2: Vague Complaint**
```
Query type base:     +0.35
Context (unknown):   -0.10
Booking reference:   +0.00
Clarity (vague):     -0.10
Sentiment (negative):-0.20
─────────────────────────
Total:                -0.05  → clamped to 0.00
```
Result: **Confidence 0.00** → **escalate**

### Action Thresholds

Based on the confidence score, the system routes the message:

- **Confidence ≥ 0.85** → `auto_send`: Sent directly to the guest without human review.
- **Confidence 0.60 – 0.84** → `agent_review`: Draft shown to an agent for approval before sending.
- **Confidence < 0.60 or complaint** → `escalate`: Routed to a human agent; AI draft is suppressed.

## Project Structure

```
app/
├── main.py                 # FastAPI application and webhooks
├── claude_service.py       # AI reply generation service
├── confidence_score.py     # Confidence calculation logic
├── utilities/
│   ├── property_utils.py   # Property information (rates, amenities)
│   ├── message_utils.py    # Message normalization and classification
│   └── __init__.py
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (not in git)

../schema.sql               # PostgreSQL schema
```

## API Endpoints

### POST /webhook/message
Receives a guest message and returns AI-drafted reply with confidence score.

**Request:**
```json
{
  "source": "whatsapp",
  "guest_name": "Rahul Sharma",
  "message": "Is the villa available from April 20 to 24?",
  "timestamp": "2026-05-05T10:30:00Z",
  "booking_ref": "NIS-2024-0891",
  "property_id": "villa-b1"
}
```

**Response:**
```json
{
  "message_id": "uuid",
  "query_type": "pre_sales_availability",
  "drafted_reply": "Hi Rahul! Villa B1 is available April 20-24...",
  "confidence_score": 0.91,
  "action": "auto_send"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Database Schema

The PostgreSQL schema supports:
- Guest profiles unified across channels
- Conversations linked to guests and reservations
- All inbound and outbound messages with AI metadata
- Audit trail of agent edits
- Confidence scores and query types per message

See `schema.sql` for full schema design with detailed comments.

## Configuration

Environment variables in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...          # Claude API key
```

## Future Enhancements

- Multi-language support for international guests
- Integration with booking platforms (Booking.com, Airbnb APIs)
- Agent dashboard for message review and analytics
- Feedback loop to improve AI model accuracy
- SMS and email channel support
- Real-time agent notifications

## License

Proprietary - Nistula 2026
