# PART 3 - THINKING QUESTIONS

---

## Question A - The Immediate Response

**What should the AI reply right now at 3 am? Write the actual message.**

### My Thinking:

> Hi [Guest Name], I'm really sorry. No hot water at 3 am with guests arriving is completely unacceptable, and I understand your frustration.
>
> I've immediately alerted our caretaker and property manager. Someone will contact you within the next 15 minutes with a resolution.
>
> We are taking your refund request seriously. It will be reviewed first thing, and you'll have a confirmed answer before 7 am.
>
> Please don't hesitate to message here if anything else comes up tonight.

**Question B - The System Design** → **## Question B - The System Design** the platform do beyond sending a message? Walk through the full system response: what gets triggered, who gets notified, what gets logged, What happens if no human responds within 30 minutes?**My Thinking:**

Sending the message is the smallest part. Here's what the platform triggers simultaneously:**Immediate (0–2 mins):**

*   Confidence score flags this as a complaint to escalate. An AI reply is sent, but no auto-resolution is attempted.
    
*   Push notification + SMS send to the caretaker (on-call 8 am–10 pm, so an override alert) and the property manager.
    
*   Incident ticket created in the internal dashboard: **guest name**, **property**, **issue type = maintenance/hot\_water**, **severity = high (guest count + breakfast deadline detected from message context)**.
    
*   The conversation is locked - no further AI auto-replies until a human takes ownership of the thread.
    

**Logged to the incident record:**Timestamp, raw message, confidence score, query classification, which humans were notified and when, and the AI-drafted reply that was sent.

**If no human responds within 30 minutes:**Escalation tier 2 fires - the owner or senior manager gets called, not just messaged. The system also sends the guest a proactive update: _"We're still working to reach someone -here's the emergency contact number."_ The guest should never sit in silence. After 60 minutes with no human response, the system auto-approves a partial refund for that night as a goodwill gesture, logs it, and notifies the owner.

**Question C - The Learning**

This is the third time in two months a guest has complained about hot water at Villa B1. What should the system do with this pattern? What would you build to prevent this complaint from happening a fourth time?**My Thinking:**

Three hot water complaints in two months is not a guest problem - it's a property problem. The system is failing to surface.

**What the system should do immediately:**Flag Villa B1 as a "repeat issue property" for hot water. Auto-generate a maintenance report and send it to the owner with all three incident timestamps, guest messages, and any refunds paid out. Make the cost of inaction visible - if each complaint costs ₹5,000 in refunds and goodwill, the report says ₹15,000 is lost to one unresolved issue.**What I'd build to prevent a fourth complaint:**

First, a **pre-stay checklist triggers -** 24 hours before every check-in at Villa B1, the caretaker gets an automated task: "Run hot water in all bathrooms. Confirm working." This takes two minutes and catches the problem before the guest does.

Second, a **pattern intelligence layer** - the system should tag complaints by issue type, not just query type. When the same tag appears 3+ times on one property within 60 days, it auto-raises a maintenance\_alert to the owner with a suggested action, not just a notification. The difference matters: a notification gets dismissed; a suggested action ("Schedule boiler inspection - 3 incidents logged") creates accountability.

Third, a **post-resolution check** - after any maintenance complaint is closed, the system schedules a follow-up message to the next guest after check-in: _"How's everything with the property so far?"_ This creates an early warning system before a complaint escalates.

The goal is to shift the platform from **responding to complaints** to **preventing them**.