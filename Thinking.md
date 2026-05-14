# Part 3 — Thinking Questions

---

## Question A — The Immediate Response

**What should the AI reply right now at 3 am? Write the actual message.**

### Answer

> Hi [Guest Name], I'm really sorry. No hot water at 3 am with guests arriving is completely unacceptable, and I understand your frustration.
>
> I've immediately alerted our caretaker and property manager. Someone will contact you within the next 15 minutes with a resolution.
>
> We are taking your refund request seriously. It will be reviewed first thing, and you'll have a confirmed answer before 7 am.
>
> Please don't hesitate to message here if anything else comes up tonight.

---

## Question B — The System Design

**What should the platform do beyond sending a message? Walk through the full system response: what gets triggered, who gets notified, what gets logged, and what happens if no human responds within 30 minutes?**

### Answer

Sending the message is the smallest part. Here's what the platform triggers simultaneously.

#### Immediate Actions (0–2 mins)

- Confidence score flags this as a complaint to escalate. An AI reply is sent, but no auto-resolution is attempted.
- Push notification + SMS sent to the caretaker (on-call override alert) and the property manager.
- Incident ticket created in the internal dashboard with the following fields:
  - **Guest Name**
  - **Property**
  - **Issue Type:** `maintenance/hot_water`
  - **Severity:** `High` *(guest count + breakfast deadline detected from message context)*
- The conversation is **locked** — no further AI auto-replies until a human takes ownership of the thread.

#### Logged to the Incident Record

- Timestamp
- Raw guest message
- Confidence score
- Query classification
- Which humans were notified and when
- The AI-drafted reply that was sent

#### If No Human Responds Within 30 Minutes

**Escalation Tier 2 fires:**

- The owner or senior manager gets **called**, not just messaged.
- The guest receives a proactive update:
  > *"We're still working to reach someone — here's the emergency contact number."*
- The guest should never sit in silence.

**After 60 minutes with no human response:**

- The system auto-approves a **partial refund** for that night as a goodwill gesture.
- The refund is logged and the owner is notified.

---

## Question C — The Learning

**This is the third time in two months a guest has complained about hot water at Villa B1. What should the system do with this pattern? What would you build to prevent this complaint from happening a fourth time?**

### Answer

Three hot water complaints in two months is not a guest problem — it's a property problem the system is failing to surface.

#### What the System Should Do Immediately

Flag Villa B1 as a **"repeat issue property"** for hot water. Auto-generate a maintenance report and send it to the owner containing:

- All three incident timestamps
- The original guest messages
- Any refunds paid out

Make the **cost of inaction visible** — if each complaint costs ₹5,000 in refunds and goodwill, the report clearly states: *"₹15,000 lost to one unresolved issue."*

#### What I'd Build to Prevent a Fourth Complaint

**1. Pre-Stay Checklist**

24 hours before every check-in at Villa B1, the caretaker receives an automated task:

> *"Run hot water in all bathrooms. Confirm working."*

This takes two minutes and catches the problem before the guest does.

**2. Pattern Intelligence Layer**

The system should tag complaints by **issue type**, not just query type. When the same tag appears 3+ times on one property within 60 days, it auto-raises a `maintenance_alert` to the owner with a **suggested action**, not just a notification.

The difference matters: a notification gets dismissed; a suggested action creates accountability.

> *Example: "Schedule boiler inspection — 3 incidents logged"*

**3. Post-Resolution Follow-Up**

After any maintenance complaint is closed, the system schedules a follow-up message to the **next guest after check-in**:

> *"How's everything with the property so far?"*

This creates an early warning system before a complaint escalates.