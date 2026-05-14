-- ============================================================================
-- NISTULA UNIFIED MESSAGING PLATFORM - PostgreSQL Schema
-- ============================================================================

-- ============================================================================
-- TABLE 1: GUESTS
-- ============================================================================
-- Purpose: One-to-one guest records across all channels
-- Design Decision: Unified guest table ensures no duplicates even if same person books via WhatsApp and also through Airbnb. Email is unique key. JSONB metadata stores channel-specific IDs (WhatsApp phone, Booking.com ID).
-- ============================================================================

CREATE TABLE guests (
    guest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core guest info
    email VARCHAR(255),
    phone VARCHAR(20),
    guest_name VARCHAR(255) NOT NULL,
    
    -- Which channel did we first contact them on?
    primary_channel VARCHAR(50),
    
    -- Channel-specific metadata stored as JSON
    -- Example: {"whatsapp_number": "+919876543210", "booking_com_id": "12345", "airbnb_id": "67890"}
    channel_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint on email to prevent duplicates
    CONSTRAINT unique_guest_email UNIQUE (email),
    
    -- Indexes for fast lookups
    INDEX idx_guest_email (email),
    INDEX idx_guest_name (guest_name)
);

COMMENT ON TABLE guests IS 'Guest profiles unified across all channels (WhatsApp, Booking.com, Airbnb, Instagram, Direct)';
COMMENT ON COLUMN guests.channel_metadata IS 'JSONB stores channel-specific identifiers to link guest across platforms';


-- ============================================================================
-- TABLE 2: RESERVATIONS
-- ============================================================================
-- Purpose: Track guest bookings linked to guests
-- Design Decision: Separate from messages because a guest can have multiple reservations, and a conversation might span multiple reservations.
-- ============================================================================

CREATE TABLE reservations (
    reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign key to guests
    guest_id UUID NOT NULL REFERENCES guests(guest_id) ON DELETE CASCADE,
    
    -- Property and booking info
    property_id VARCHAR(50) NOT NULL,  -- e.g., villa-b1
    booking_ref VARCHAR(100) NOT NULL,  -- e.g., NIS-2024-0891
    
    -- Dates and guest count
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    num_adults INT NOT NULL DEFAULT 1,
    num_children INT DEFAULT 0,
    num_nights INT GENERATED ALWAYS AS (check_out_date - check_in_date) STORED,
    
    -- Booking status
    booking_status VARCHAR(50) DEFAULT 'pending',  -- pending, confirmed, cancelled
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint on booking_ref
    CONSTRAINT unique_booking_ref UNIQUE (booking_ref),
    
    -- Indexes
    INDEX idx_guest_reservations (guest_id),
    INDEX idx_property_reservations (property_id),
    INDEX idx_booking_ref (booking_ref)
);

COMMENT ON TABLE reservations IS 'Guest reservations/bookings linked to guests and properties';
COMMENT ON COLUMN reservations.num_nights IS 'Auto-calculated field for reporting and analytics';


-- ============================================================================
-- TABLE 3: CONVERSATIONS
-- ============================================================================
-- Purpose: Group related messages into conversations
-- Design Decision: Conversations can span multiple channels (guest might start on WhatsApp, continue on email). Each conversation has one guest, one channel source, but can be linked to a reservation (or pre-booking conversation).
-- ============================================================================

CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign keys
    guest_id UUID NOT NULL REFERENCES guests(guest_id) ON DELETE CASCADE,
    reservation_id UUID REFERENCES reservations(reservation_id) ON DELETE SET NULL,
    
    -- Context
    property_id VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,  -- whatsapp, booking_com, airbnb, instagram, direct
    
    -- Conversation state
    conversation_status VARCHAR(50) DEFAULT 'open',  -- open, closed, resolved
    conversation_topic VARCHAR(255),  -- e.g., "Booking inquiry for April 20-24"
    
    -- Activity tracking
    message_count INT DEFAULT 0,
    last_message_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_guest_conversations (guest_id),
    INDEX idx_property_conversations (property_id),
    INDEX idx_status (conversation_status),
    INDEX idx_last_message (last_message_at)
);

COMMENT ON TABLE conversations IS 'Groups related messages. A guest can have multiple conversations across different channels or time periods.';
COMMENT ON COLUMN conversations.source IS 'Denormalized from messages for quick filtering';


-- ============================================================================
-- TABLE 4: MESSAGES (Core table - All inbound + outbound messages)
-- ============================================================================
-- Purpose: Store every message with AI metadata, edits, and response tracking
-- Design Decision: Single table for both inbound and outbound keeps conversation flow clear. AI metadata (query_type, confidence_score, action) stored for every message for auditability and learning.
-- ============================================================================

CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign keys
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    guest_id UUID NOT NULL REFERENCES guests(guest_id) ON DELETE CASCADE,
    reservation_id UUID REFERENCES reservations(reservation_id) ON DELETE SET NULL,
    
    -- Message context
    property_id VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,  -- whatsapp, booking_com, airbnb, instagram, direct, email
    message_type VARCHAR(20) NOT NULL,  -- inbound (from guest), outbound (to guest)
    
    -- Message content
    message_text TEXT NOT NULL,
    
    -- =========================================================================
    -- AI PROCESSING METADATA (Filled only for inbound messages)
    -- =========================================================================
    query_type VARCHAR(50),  
    -- Values: pre_sales_availability, pre_sales_pricing, post_sales_checkin, 
    -- special_request, complaint, general_enquiry
    
    -- Confidence score calculated by our 5-factor model
    confidence_score DECIMAL(3, 2),  -- 0.00 to 1.00
    
    -- Action determined by confidence score
    action VARCHAR(50),  -- auto_send, agent_review, escalate
    
    -- =========================================================================
    -- AI DRAFT & RESPONSE TRACKING
    -- =========================================================================
    -- This is the AI-generated draft reply (stored for audit trail)
    ai_drafted_reply TEXT,
    
    -- Flags to track message lifecycle
    is_ai_drafted BOOLEAN DEFAULT FALSE,  -- Was there an AI draft?
    is_agent_edited BOOLEAN DEFAULT FALSE,  -- Did agent edit the AI draft?
    is_auto_sent BOOLEAN DEFAULT FALSE,  -- Was response auto-sent without review?
    
    -- What was actually sent to the guest (may differ from AI draft if edited)
    final_reply TEXT,
    
    -- =========================================================================
    -- RESPONSE STATUS & AUDIT
    -- =========================================================================
    response_status VARCHAR(50) DEFAULT 'pending',  -- pending, sent, read, error
    responded_at TIMESTAMP,  -- When was response sent?
    responded_by VARCHAR(255),  -- 'ai_auto' or agent name
    response_time_minutes INT,  -- How long to respond? (for SLA tracking)
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_conversation (conversation_id),
    INDEX idx_guest (guest_id),
    INDEX idx_reservation (reservation_id),
    INDEX idx_created (created_at),
    INDEX idx_action (action),  -- For finding messages needing agent review
    INDEX idx_query_type (query_type),  -- For analytics
    INDEX idx_responded (responded_at),  -- For response time analytics
    INDEX idx_status (response_status)  -- For finding unresponded messages
);

COMMENT ON TABLE messages IS 'All messages (inbound + outbound) with AI processing metadata for audit and optimization';
COMMENT ON COLUMN messages.query_type IS 'Classification of inbound message (6 types). Null for outbound messages.';
COMMENT ON COLUMN messages.confidence_score IS 'AI confidence 0.0-1.0 calculated by 5-factor model. Determines if auto_send, agent_review, or escalate.';
COMMENT ON COLUMN messages.ai_drafted_reply IS 'CRITICAL FOR AUDIT: Stores what AI generated, even if agent edited it. Enables learning and compliance.';
COMMENT ON COLUMN messages.final_reply IS 'What was actually sent to guest. May differ from AI draft if agent edited.';
COMMENT ON COLUMN messages.is_ai_drafted IS 'Flag: Was there an AI draft for this message?';
COMMENT ON COLUMN messages.is_agent_edited IS 'Flag: Did agent edit the AI draft before sending?';
COMMENT ON COLUMN messages.is_auto_sent IS 'Flag: Was response auto-sent (confidence >= 0.85) without human review?';


-- ============================================================================
-- TABLE 5: MESSAGE_EDITS (Audit trail)
-- ============================================================================
-- Purpose: Track all edits to message drafts for compliance and improvement
-- Design Decision: Separate audit table allows unlimited edit history without bloating main messages table. Also enables analysis of what agents change.
-- ============================================================================

CREATE TABLE message_edits (
    edit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Which message was edited?
    message_id UUID NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
    
    -- Who made the edit?
    edited_by VARCHAR(255) NOT NULL,  -- agent name or system user
    
    -- Before and after
    original_reply TEXT NOT NULL,  -- AI-generated draft
    edited_reply TEXT NOT NULL,  -- Agent's edit
    
    -- Metadata
    edit_reason VARCHAR(500),  -- Why did agent edit? (optional)
    edit_type VARCHAR(50),  -- typo_fix, tone_adjustment, information_correction, completeness_addition
    
    -- Timestamp
    edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Index
    INDEX idx_message_edits (message_id),
    INDEX idx_agent_edits (edited_by),
    INDEX idx_edit_time (edited_at)
);

COMMENT ON TABLE message_edits IS 'Audit trail of agent edits to AI-drafted replies. Used for compliance and model improvement.';
COMMENT ON COLUMN message_edits.edit_type IS 'Categorization of what changed helps identify patterns and retrain AI';


-- ============================================================================
-- TABLE 6: CHANNEL_MAPPINGS
-- ============================================================================
-- Purpose: Track unique channel identifiers per guest
-- Design Decision: Separate table (not JSONB) allows easy querying of guests by channel ID (e.g., "find guest by WhatsApp number") without JSONB functions.
-- ============================================================================

CREATE TABLE channel_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    guest_id UUID NOT NULL REFERENCES guests(guest_id) ON DELETE CASCADE,
    
    -- Channel and identifier
    channel VARCHAR(50) NOT NULL,  -- whatsapp, booking_com, airbnb, instagram, direct, email
    channel_identifier VARCHAR(255) NOT NULL,  -- Phone, email, booking ID, etc.
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint: one identifier per channel per guest
    CONSTRAINT unique_channel_mapping UNIQUE (guest_id, channel, channel_identifier),
    
    -- Indexes
    INDEX idx_channel_identifier (channel, channel_identifier),  -- Fast reverse lookup
    INDEX idx_guest_channels (guest_id)
);

COMMENT ON TABLE channel_mappings IS 'Maps channel-specific identifiers (phone, email, booking ID) to guests for deduplication';


-- ============================================================================
-- DESIGN DECISION EXPLANATION: AI Draft Storage
-- ============================================================================
/*
HARDEST DESIGN DECISION: Store both AI-drafted reply AND final reply?

THE DILEMMA:
Should we store ONLY the final response sent to guest, or store BOTH the
AI draft and what the agent modified it to?

WHY IT'S HARD:
- Storing both uses more storage (+1 text column per message)
- But discarding the AI draft loses critical information

WHY WE STORE BOTH (AI DRAFT + FINAL REPLY):

1. COMPLIANCE & AUDIT
   Regulators/legal may need to prove: "Did AI suggest something harmful?"
   Answer: Check ai_drafted_reply column. If agent changed dangerous content,
   the is_agent_edited flag shows human oversight kicked in.

2. MODEL IMPROVEMENT
   Our AI gets smarter by learning from agent edits.
   - If agent always removes certain words → retrain model to avoid them
   - If agent adds info AI missed → identify knowledge gaps
   - If agent keeps AI draft unchanged 95% of the time → AI is doing well
   
   We can't do this analysis if we only store the final reply.

3. DEBUGGING ISSUES
   If a guest complains "Your AI was rude" → we can see EXACTLY what AI
   suggested. If it was the agent who made it rude (by editing), we know.

TRADE-OFF ACCEPTED:
Yes, +1 TEXT column per message. But:
- Cost: ~20KB per message * 100K messages = 2GB extra (negligible)
- Value: Regulatory compliance + AI optimization = priceless

ALTERNATIVE (rejected):
Store AI draft in separate table? No - performance overhead of JOIN.
The draft should be 1:1 with message so always fetched together.
*/

-- ============================================================================
-- VIEWS for common queries
-- ============================================================================

-- View 1: Unresponded messages needing attention
CREATE VIEW messages_pending_response AS
SELECT 
    m.message_id,
    g.guest_name,
    c.source,
    m.message_text,
    m.query_type,
    m.confidence_score,
    m.action,
    m.ai_drafted_reply,
    m.created_at,
    EXTRACT(EPOCH FROM (NOW() - m.created_at)) / 60 AS minutes_waiting
FROM messages m
JOIN guests g ON m.guest_id = g.guest_id
JOIN conversations c ON m.conversation_id = c.conversation_id
WHERE m.response_status = 'pending'
AND m.message_type = 'inbound'
ORDER BY m.created_at ASC;

-- View 2: Agent edit frequency (for AI improvement)
CREATE VIEW agent_edit_analysis AS
SELECT 
    m.query_type,
    COUNT(me.edit_id) AS total_edits,
    COUNT(DISTINCT m.message_id) AS total_messages_edited,
    ROUND(100.0 * COUNT(me.edit_id) / 
        (SELECT COUNT(*) FROM messages WHERE is_ai_drafted = TRUE), 2) AS edit_percentage,
    ARRAY_AGG(DISTINCT me.edit_type) AS edit_types
FROM messages m
LEFT JOIN message_edits me ON m.message_id = me.message_id
WHERE m.is_ai_drafted = TRUE
GROUP BY m.query_type
ORDER BY total_edits DESC;
