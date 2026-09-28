# D Web Studio — Outreach Memory

## Memory & Persistent State Specification

---

# 1. Purpose

`memory.md` defines the persistent memory system for the D Web Studio outreach automation.

The memory system allows the application to remember:

* Lead information
* Previous outreach
* Message history
* Delivery status
* AI decisions
* Verified information
* Errors
* Replies
* Follow-up state
* Campaign configuration
* Learning signals

The goal is simple:

> **The system should remember what has already happened so it does not repeat work, lose progress, or make the same mistake again.**

---

# 2. Memory Principle

The system should follow:

```text
OBSERVE
   ↓
STORE
   ↓
RECALL
   ↓
DECIDE
   ↓
ACT
   ↓
STORE RESULT
```

Memory is persistent across application restarts.

---

# 3. Source of Truth

Runtime memory should be stored locally.

Recommended:

```text
SQLite
```

Example:

```text
data/outreach.db
```

Excel remains the human-readable lead source/import/export.

```text
Excel = Lead input / export
SQLite = Runtime memory / source of truth
```

---

# 4. Memory Layers

The system should separate memory into layers.

```text
┌─────────────────────────────┐
│       System Memory         │
│ Campaign rules / settings   │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│       Lead Memory           │
│ Identity / qualification    │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│     Outreach Memory         │
│ Emails / WhatsApp / replies │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│       AI Memory             │
│ Decisions / strategies      │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│      Learning Memory        │
│ Outcomes / patterns        │
└─────────────────────────────┘
```

---

# 5. Lead Memory

Each lead should have a persistent record.

Example:

```text
Lead
├── Identity
├── Contact Information
├── Qualification
├── Outreach State
├── AI Context
└── History
```

Recommended fields:

```text
id
name
email
phone
city
gender
age
education
source
priority
```

---

# 6. Lead Identity

The system needs a stable way to recognize the same lead.

Preferred identity order:

```text
1. Existing internal lead ID
2. Email
3. Normalized phone number
4. Combination of name + phone/email
```

The system should normalize:

* Phone formatting
* Email casing
* Whitespace
* Common formatting differences

Example:

```text
+91 98765 43210
```

and:

```text
9876543210
```

may represent the same number after normalization.

The system must avoid creating duplicate lead records when identity can be confidently matched.

---

# 7. Verified Information

Each important piece of information should have a confidence state.

```text
VERIFIED
UNVERIFIED
UNKNOWN
```

Example:

```text
Name:
VERIFIED

Business:
UNKNOWN

LinkedIn profile:
UNVERIFIED
```

The AI must use these states when generating messages.

---

# 8. Verification Source

When useful, store where information came from.

Example:

```text
Source:
Excel

Source:
Official Website

Source:
LinkedIn

Source:
User Confirmed
```

Recommended fields:

```text
fact
value
verification_status
source
verified_at
```

---

# 9. Outreach Memory

Every outreach action should be remembered.

Example:

```text
Lead: Rohit Kumar

Email:
SENT

WhatsApp:
SENT
```

Recommended fields:

```text
channel
action
status
timestamp
message_id
template_version
error
```

---

# 10. Message History

The system should remember what message was sent.

Example:

```text
2026-09-28

Channel:
Email

Template:
EMAIL_V2

Status:
SENT

Message ID:
provider-message-id
```

For privacy and storage efficiency, the system may store either:

* The full message
* A message snapshot
* A message hash + template version

depending on implementation requirements.

---

# 11. Duplicate Protection Memory

Memory must be consulted before every send.

Example:

```text
Lead:
Rohit Kumar

Email:
SENT
```

New run:

```text
AI:
Send email.

System:
Email already SENT.

Action:
SKIP
```

The AI must never override this rule.

---

# 12. Partial Completion Memory

The system must remember individual channel states.

Example:

```text
Email:
SENT

WhatsApp:
PENDING
```

After restart:

```text
Email:
SKIP

WhatsApp:
PROCESS
```

This is one of the most important memory requirements.

---

# 13. Run Memory

Every automation run should have a run ID.

Example:

```text
Run ID:
2026-09-28-001
```

Store:

```text
run_id
started_at
ended_at
status
total_leads
completed
failed
skipped
```

This makes previous automation runs traceable.

---

# 14. Current Run State

The application should persist enough information to recover from interruption.

Example:

```text
Current Run:
RUNNING

Current Lead:
Rohit Kumar

Current Action:
EMAIL

Progress:
12 / 70
```

If the application closes unexpectedly, the next startup can reconstruct the state from the database.

---

# 15. AI Memory

The AI should remember useful decisions.

Example:

```text
Lead Type:
PROFESSIONAL

Confidence:
MEDIUM

Strategy:
GENERIC_PROFESSIONAL

Personalization:
Name only
```

Store the decision with:

```text
lead_id
decision
reason
confidence
created_at
```

---

# 16. AI Memory Must Be Evidence-Based

The AI must not store speculation as fact.

Bad:

```text
Rohit owns a coaching institute.
```

when there is no evidence.

Better:

```text
Possible coaching-related profile found.
Verification: UNVERIFIED.
```

AI memory should distinguish:

```text
FACT
INFERENCE
UNKNOWN
```

---

# 17. AI Decision Memory

For each meaningful AI decision, store:

```text
Strategy
Reason
Confidence
Template
Channels
Timestamp
```

Example:

```text
Strategy:
GENERIC

Reason:
No verified business information found.

Confidence:
LOW

Template:
EMAIL_V1
```

This allows the system to understand why a message was generated.

---

# 18. Conversation Memory

If a lead replies, the reply becomes part of the lead's communication history.

Example:

```text
Lead:
Rohit Kumar

Outgoing:
"Would you be open to discussing a website requirement?"

Incoming:
"Yes, send me some examples."
```

AI classification:

```text
INTERESTED
```

Then:

```text
Automated cold outreach:
STOP
```

The user should be notified for human follow-up.

---

# 19. Reply Memory

Store reply classification:

```text
INTERESTED
QUESTION
NOT_NOW
NOT_INTERESTED
WRONG_PERSON
OPT_OUT
UNKNOWN
```

Recommended fields:

```text
lead_id
channel
reply_text
classification
timestamp
```

---

# 20. Opt-Out Memory

Opt-out is permanent unless explicitly changed by the user.

Example:

```text
Lead Status:
OPTED_OUT
```

Future automation:

```text
AI:
Contact lead.

System:
OPTED_OUT.

Action:
DO NOT CONTACT
```

This rule takes priority over AI recommendations.

---

# 21. Follow-Up Memory

The system must remember follow-ups.

Example:

```text
Initial Email:
SENT
2026-09-28

Follow-up:
PENDING
```

After sending:

```text
Follow-up:
SENT
```

The system must not send the same follow-up twice.

---

# 22. Campaign Memory

Store campaign configuration separately.

Example:

```text
Campaign:
D Web Studio Outreach

Goal:
Website / landing-page leads

Price:
₹4,999

Portfolio:
Configured portfolio URL

Channels:
Email + WhatsApp
```

Campaign configuration should be versioned when changed.

---

# 23. Template Memory

Templates should have versions.

Example:

```text
EMAIL_V1
EMAIL_V2

WHATSAPP_V1
WHATSAPP_V2
```

Every sent message should record which version was used.

Example:

```text
Lead:
Rohit Kumar

Channel:
Email

Template:
EMAIL_V2
```

---

# 24. Learning Memory

The system can store aggregate outcomes.

Example:

```text
Template:
EMAIL_V2

Sent:
100

Replies:
8

Interested:
3
```

This allows future AI decisions to consider actual campaign history.

---

# 25. Learning Does Not Mean Automatic Assumptions

The AI should not conclude that one template is universally better from a tiny sample.

Example:

```text
Template A:
5 messages
2 replies
```

This is not enough evidence to permanently replace every other template.

The system should retain historical data.

---

# 26. Memory Retrieval

Before processing a lead, retrieve:

```text
Lead Information
+
Verification State
+
Previous Outreach
+
Previous Replies
+
Current Status
+
AI Decision History
+
Campaign Rules
```

Conceptually:

```text
Lead ID
   ↓
Memory Retrieval
   ↓
Context Builder
   ↓
AI
```

---

# 27. Context Builder

The Context Builder prepares the minimum useful information for the AI.

Example:

```text
LEAD
Name: Rohit Kumar
City: Bareilly
Education: Diploma in Electronics Engineering

VERIFICATION
Business: UNKNOWN

OUTREACH
Email: PENDING
WhatsApp: PENDING

HISTORY
No previous contact.

CAMPAIGN
Offer: Website / Landing Page
Starting price: ₹4,999
```

The AI receives this structured context instead of raw database dumps.

---

# 28. Memory Size Control

Do not send the entire lead history to the AI every time.

Use:

```text
Relevant recent history
+
Important persistent facts
+
Current campaign context
```

This reduces:

* Token usage
* Processing time
* AI cost
* Noise

---

# 29. Memory Priority

When conflicting information exists:

```text
1. User-confirmed information
2. Verified source
3. Recent reliable source
4. Existing lead record
5. AI inference
6. Unknown
```

Never let an AI inference overwrite verified information automatically.

---

# 30. Memory Update Rules

Memory should be updated when:

```text
Lead imported
Lead information changes
Email sent
WhatsApp sent
Message fails
Reply received
Opt-out received
AI decision made
Campaign configuration changes
Automation run starts
Automation run finishes
```

---

# 31. Atomic Updates

Important state changes should be saved atomically.

Example:

```text
Email successfully sent
        ↓
Database transaction
        ↓
Email Status = SENT
        ↓
Message ID saved
        ↓
Timestamp saved
```

If the database update fails, the system should handle the uncertain state carefully rather than blindly sending again.

---

# 32. Uncertain Delivery State

External APIs can sometimes return uncertain results.

Example:

```text
Request sent
   ↓
Network timeout
   ↓
Unknown whether provider received it
```

Do not immediately assume:

```text
FAILED
```

when the delivery result is genuinely unknown.

Possible internal state:

```text
UNKNOWN
```

The system should use provider message IDs or reconciliation where supported before retrying.

This reduces accidental duplicate messages.

---

# 33. Memory and Excel Sync

When Excel is re-imported:

```text
Excel
  ↓
Compare with Local DB
  ↓
Update changed lead information
  ↓
Preserve outreach history
```

Never overwrite:

```text
Email Status
WhatsApp Status
Message History
Reply History
Opt-Out
```

just because the Excel file contains older values.

---

# 34. Example Memory Record

```text
Lead:
Rohit Kumar

Identity:
lead_00042

Contact:
Email: sample.lead@example.com
Phone: 9000000000

Qualification:
City: Sample City
Education: Diploma in Electronics Engineering

Verification:
Business: UNKNOWN

Outreach:
Email: SENT
WhatsApp: SENT

Last Contact:
2026-09-28

Template:
EMAIL_V1
WHATSAPP_V1

AI Strategy:
GENERIC_PROFESSIONAL

Lead Status:
COMPLETED
```

---

# 35. Memory Lifecycle

```text
IMPORT
  ↓
CREATE MEMORY
  ↓
ENRICH
  ↓
CONTACT
  ↓
STORE RESULT
  ↓
REPLY / NO REPLY
  ↓
FOLLOW-UP
  ↓
OUTCOME
  ↓
LEARNING
```

---

# 36. Memory Cleanup

Memory should not grow without control.

Possible cleanup rules:

* Compress old activity logs.
* Archive old campaigns.
* Keep important lead history.
* Remove temporary AI context.
* Keep delivery records required for duplicate protection.

Do not delete important communication history simply to reduce database size.

---

# 37. Memory Backup

The local database should be easy to back up.

Recommended:

```text
data/outreach.db
```

Backup:

```text
data/backups/
```

Possible strategy:

```text
Before major campaign
       ↓
Create DB backup
       ↓
Run automation
```

The system should never automatically upload backups to an external service unless explicitly configured.

---

# 38. Memory Security

Memory may contain personal contact information.

Therefore:

* Keep database local.
* Do not expose it publicly.
* Do not commit it to Git.
* Protect local files.
* Avoid unnecessary duplication.
* Do not include credentials in memory.
* Do not expose private data in logs.

---

# 39. Memory + AI Privacy

Only send necessary context to an AI provider.

For example, if the AI only needs:

```text
Name
City
Verified profession
Previous outreach
```

do not send unrelated database fields.

Credentials must never be part of AI context.

---

# 40. Memory Failure

If memory/database access fails:

```text
Memory unavailable
       ↓
STOP AUTOMATED SEND
       ↓
Show ERROR
       ↓
Protect against duplicate messages
```

The system should prefer stopping safely over sending without reliable state.

---

# 41. Memory Rules

The following rules are mandatory:

```text
1. Never forget a successful send.
2. Never overwrite delivery history accidentally.
3. Never treat an assumption as a verified fact.
4. Never send if duplicate state cannot be checked.
5. Never contact an opted-out lead.
6. Never lose partial progress.
7. Never store credentials in lead memory.
8. Preserve message/template versions.
9. Keep important events timestamped.
10. Keep runtime memory local.
```

---

# 42. Memory Architecture

```text
                    ┌─────────────────────┐
                    │     Lead Memory     │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
      ┌────────────┐    ┌────────────┐    ┌────────────┐
      │ Outreach   │    │ AI Memory  │    │ Reply      │
      │ History    │    │ Decisions  │    │ History    │
      └─────┬──────┘    └─────┬──────┘    └─────┬──────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              ▼
                    ┌─────────────────────┐
                    │    SQLite Memory    │
                    │    Source of Truth  │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        Automation Engine               AI Context
                │                             │
                ▼                             ▼
        Email / WhatsApp                AI Decision
```

---

# 43. Memory vs AI

Memory and AI are different systems.

### Memory

Answers:

> What happened before?

### AI

Answers:

> Given what we know, what should we do next?

### Automation Engine

Answers:

> Is this action allowed, and how do we execute it safely?

The relationship is:

```text
MEMORY
  ↓
AI
  ↓
DECISION
  ↓
SYSTEM VALIDATION
  ↓
AUTOMATION
  ↓
NEW MEMORY
```

---

# 44. Final Memory Principle

The entire system should follow:

> **Remember facts, remember actions, remember outcomes, distinguish facts from assumptions, and never lose the state required to safely continue.**

The AI can become smarter over time, but the memory system must remain predictable, auditable, and reliable.
