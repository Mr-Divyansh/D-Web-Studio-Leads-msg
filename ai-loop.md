# D Web Studio — AI Outreach Loop

## AI Decision & Automation Specification

---

# 1. Purpose

The AI Loop is the intelligence layer of the D Web Studio outreach system.

Its job is to help the system:

* Understand lead information
* Decide how a lead should be approached
* Personalize messages
* Select the appropriate outreach channel
* Detect missing or unreliable information
* Learn from previous outreach results
* Improve future message generation
* Avoid repeating mistakes
* Continue processing leads without requiring manual decisions for every lead

The AI Loop does **not** replace the automation engine.

The automation engine controls execution.

The AI Loop provides intelligence.

```text
Automation Engine
        ↓
AI Loop
        ↓
Decision
        ↓
Automation Engine
        ↓
Email / WhatsApp
```

---

# 2. Core Principle

The AI should follow this loop:

```text
OBSERVE
   ↓
UNDERSTAND
   ↓
DECIDE
   ↓
GENERATE
   ↓
EXECUTE
   ↓
OBSERVE RESULT
   ↓
EVALUATE
   ↓
IMPROVE
   ↓
NEXT LEAD
```

The system should not blindly send the same message to every lead.

---

# 3. AI Responsibilities

The AI layer may perform:

```text
Lead Understanding
Message Personalization
Channel Selection
Message Generation
Message Quality Checking
Result Analysis
Pattern Detection
Template Improvement
```

The AI should NOT directly control sensitive infrastructure.

It should not independently:

* Change API credentials
* Modify authentication
* Delete lead data
* Change database schemas
* Disable safety checks
* Bypass duplicate protection
* Send messages outside the configured automation workflow

---

# 4. AI Input

For every lead, the AI receives only the information necessary to make the outreach decision.

Example:

```text
Name
Email
Phone
Priority
City
Education
Source
Verified business information
Previous outreach status
Previous outreach result
```

Example input:

```text
Name: Rohit Kumar
City: Bareilly
Education: Diploma in Electronics Engineering
Priority: Yes
Email: available
Phone: available
Previous Contact: None
```

---

# 5. Verified Information Rule

The AI must distinguish between:

```text
VERIFIED
UNVERIFIED
UNKNOWN
```

Example:

```text
Verified:
Name from lead database

Unverified:
Possible LinkedIn profile

Unknown:
Whether the person currently owns a business
```

The AI must never convert an assumption into a fact.

---

# 6. Lead Understanding

Before generating a message, the AI should classify the available information.

Example:

```text
Lead Type:
Professional / Business / Unknown

Confidence:
High / Medium / Low

Known Need:
Website / Unknown

Personalization Available:
Name / City / Profession / Business
```

If insufficient information exists, use a generic professional message rather than inventing context.

---

# 7. Lead Classification

Possible categories:

```text
BUSINESS_OWNER
PROFESSIONAL
FREELANCER
JOB_SEEKER
STUDENT
UNKNOWN
```

Classification must be based only on available evidence.

The AI should not make strong claims from weak information.

---

# 8. Outreach Intent

The primary outreach goal is:

> Identify whether the lead may have a web-development requirement and start a conversation.

The AI should not attempt to force a sale.

The message should be:

* Short
* Clear
* Relevant
* Professional
* Human-sounding

---

# 9. Message Strategy

The AI should choose a message strategy based on available information.

## Strategy A — Verified Business

If a business is confidently verified:

```text
Business-specific outreach
```

Example structure:

```text
Hi {{name}},

I came across {{business}} and noticed an opportunity to improve its online presence.

I build modern websites and landing pages for businesses.

If you're considering a website or improving your current one, I’d be happy to share a quick idea.

— Divyansh
D Web Studio
```

---

## Strategy B — Verified Professional

If the person's professional identity is known:

```text
Professional outreach
```

The message should focus on:

* Personal website
* Portfolio
* Landing page
* Professional online presence

---

## Strategy C — Unknown Identity

If the identity cannot be confidently verified:

```text
Generic outreach
```

Do not pretend to know the person's business.

Example:

```text
Hi {{name}},

I’m Divyansh from D Web Studio. I build modern websites and landing pages for businesses and professionals.

If you’re currently looking for web development work, I’d be happy to help.

Landing pages start from ₹4,999.

Portfolio:
{{portfolio}}

Would you be open to discussing a website requirement?

— Divyansh
```

---

# 10. Channel Selection

The AI may recommend:

```text
EMAIL
WHATSAPP
BOTH
SKIP
```

However, the automation engine remains responsible for enforcing channel availability and status.

Example:

```text
AI Decision:
BOTH

System:
Email = SENT
WhatsApp = NOT_AVAILABLE

Result:
Only Email processed
```

---

# 11. Channel Priority

Default channel order:

```text
1. Email
2. WhatsApp
```

This can be configured.

The AI may recommend a different approach when justified by available information, but it must not bypass system rules.

---

# 12. Message Generation Pipeline

Message generation follows:

```text
Lead Data
   ↓
Lead Classification
   ↓
Available Evidence
   ↓
Outreach Strategy
   ↓
Draft Message
   ↓
Quality Check
   ↓
Final Message
```

---

# 13. Message Quality Check

Before sending, the AI should check:

```text
✓ Correct name
✓ No invented facts
✓ Clear purpose
✓ Short enough
✓ Professional tone
✓ No unnecessary hype
✓ Correct portfolio link
✓ Correct price
✓ No sensitive information
✓ No duplicate message
```

If the draft fails validation:

```text
Draft
 ↓
Quality Check
 ↓
FAIL
 ↓
Regenerate
 ↓
Quality Check
```

Maximum regeneration attempts should be limited.

Example:

```text
MAX_AI_RETRIES = 2
```

---

# 14. Message Length

Messages should be concise.

Recommended:

### Email

Approximately:

```text
80–150 words
```

### WhatsApp

Approximately:

```text
40–100 words
```

The exact length may change depending on context.

The AI should prioritize clarity over length.

---

# 15. Personalization

Personalization should be based on evidence.

Safe:

```text
Hi Rohit,
```

Safe when verified:

```text
I came across ABC Coaching...
```

Unsafe:

```text
I know you're struggling to get students online...
```

unless that information is actually known.

---

# 16. No Hallucinated Personalization

The AI must never fabricate:

* Company names
* Job positions
* Business problems
* Previous conversations
* Website ownership
* Customer numbers
* Revenue
* Location-specific claims
* Personal interests

If information is unknown:

```text
Use a generic message.
```

---

# 17. Outreach Memory

The AI should have access to previous outreach state.

Example:

```text
Lead:
Rohit Kumar

Previous Email:
SENT

Previous WhatsApp:
FAILED

Previous Message:
Website development offer

Result:
No reply
```

The AI should not generate an identical message on retry.

---

# 18. Follow-Up Logic

Follow-ups should only occur when explicitly enabled by the campaign configuration.

Possible sequence:

```text
Day 0
Initial outreach

Day 3+
Follow-up

Day 7+
Final follow-up
```

The AI should not automatically create unlimited follow-ups.

---

# 19. Follow-Up Rules

Before creating a follow-up:

```text
Check:
- Previous message sent?
- Reply received?
- Follow-up already sent?
- Opt-out?
- Lead status?
- Campaign configuration?
```

If the lead has replied:

```text
STOP AUTOMATED OUTREACH
```

If the lead has opted out:

```text
STOP ALL OUTREACH
```

---

# 20. Reply Detection

If email/WhatsApp reply detection is implemented, classify responses into:

```text
INTERESTED
QUESTION
NOT_NOW
NOT_INTERESTED
WRONG_PERSON
OPT_OUT
UNKNOWN
```

Example:

```text
Lead Reply:
"Yes, please send some details."

AI Classification:
INTERESTED
```

Then:

```text
Automation
   ↓
Pause automated campaign
   ↓
Notify user
```

The system should avoid continuing cold outreach after a meaningful reply.

---

# 21. Human Handoff

The AI should hand control to the user when:

```text
Lead is interested
Lead asks pricing questions
Lead requests custom work
Lead asks technical questions
Lead requests a call
Lead asks for examples
Lead wants negotiation
```

Example dashboard event:

```text
🔥 HUMAN ACTION REQUIRED

Rohit Kumar replied:
"Can you send me some examples?"
```

The AI should not automatically negotiate or make binding commitments unless explicitly configured.

---

# 22. AI Decision Object

Internally, the AI should produce a structured decision.

Example:

```text
{
  "lead_type": "PROFESSIONAL",
  "confidence": "MEDIUM",
  "strategy": "GENERIC_PROFESSIONAL",
  "channels": ["EMAIL", "WHATSAPP"],
  "personalization": {
    "name": "Rohit"
  },
  "reason": "Professional identity available but no verified business found."
}
```

The exact implementation format may differ depending on the programming language.

---

# 23. AI Must Not Override System State

Example:

```text
AI:
Send WhatsApp.

System:
WhatsApp Status = NOT_AVAILABLE.
```

Final action:

```text
DO NOT SEND
```

System state always wins over AI recommendation.

---

# 24. AI + Automation Architecture

```text
                  ┌───────────────────┐
                  │   Lead Database   │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │  Automation       │
                  │  Engine           │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │      AI Loop      │
                  │                   │
                  │ Understand        │
                  │ Decide            │
                  │ Generate          │
                  │ Validate          │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ System Validation │
                  └─────────┬─────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
          ┌──────────────┐      ┌──────────────┐
          │  Gmail API   │      │ WhatsApp API │
          └──────┬───────┘      └──────┬───────┘
                 │                     │
                 └──────────┬──────────┘
                            ▼
                  ┌───────────────────┐
                  │ Result / Status   │
                  └─────────┬─────────┘
                            │
                            ▼
                     AI Observation
                            │
                            ▼
                     Next Lead
```

---

# 25. Continuous Improvement Loop

The AI can learn from aggregate campaign results.

The loop is:

```text
Messages Sent
      ↓
Responses Collected
      ↓
Results Classified
      ↓
Patterns Identified
      ↓
Message Strategy Updated
      ↓
Future Messages Improved
```

Example:

```text
Template A
100 messages
3 replies

Template B
100 messages
8 replies
```

The AI may identify that Template B produced more replies.

However, the system should retain the underlying data and avoid treating a small sample as definitive evidence.

---

# 26. Learning Data

The AI may analyze:

```text
Message template
Channel
Lead category
Message length
Personalization type
Send time
Reply status
Reply category
```

Potential outcomes:

```text
SENT
REPLIED
INTERESTED
NOT_INTERESTED
NO_REPLY
FAILED
```

---

# 27. Learning Rules

The AI should improve based on actual observations.

It should NOT:

```text
Assume success from no response
Invent performance data
Change multiple variables without tracking them
Erase historical results
```

Every meaningful strategy change should be traceable.

---

# 28. Template Versioning

Message templates should have versions.

Example:

```text
EMAIL_TEMPLATE_V1
EMAIL_TEMPLATE_V2
WHATSAPP_TEMPLATE_V1
```

When a template changes:

```text
New Version
    ↓
New Outreach
    ↓
Store Version Used
```

This makes campaign analysis possible.

---

# 29. AI Experimentation

Future versions may support controlled experiments.

Example:

```text
50% → Template A
50% → Template B
```

Track:

```text
Template
Messages Sent
Replies
Positive Replies
```

Do not change templates randomly during a running experiment.

---

# 30. Feedback Loop

The system should collect feedback from:

### External outcome

```text
Email delivered
Email bounced
WhatsApp delivered
Reply received
No reply
```

### Human feedback

The user may mark:

```text
GOOD MESSAGE
BAD MESSAGE
WRONG PERSONALIZATION
GOOD LEAD
BAD LEAD
```

This feedback can improve future AI decisions.

---

# 31. AI Memory

AI memory should be structured rather than unlimited conversation history.

Useful memory:

```text
Campaign rules
Message templates
Verified lead facts
Previous outreach
Reply classification
User-approved strategy
```

Avoid storing unnecessary personal information.

---

# 32. Privacy

The AI should receive the minimum information required.

Do not send unrelated private data to an AI provider.

Sensitive credentials must never be included in AI prompts.

Never include:

```text
OAuth tokens
API keys
Passwords
Authentication secrets
```

---

# 33. AI Failure Handling

If the AI service fails:

```text
AI Request
   ↓
Failure
   ↓
Retry
   ↓
Failure
   ↓
Fallback Template
```

The automation should still be able to operate using a safe predefined message template.

AI should improve the system, not become a single point of failure.

---

# 34. Fallback Mode

Fallback mode uses predefined templates.

Example:

```text
IF AI unavailable:
    Use approved generic email template
    Use approved generic WhatsApp template
```

The system continues processing only if the fallback message passes normal validation.

---

# 35. AI Timeout

AI requests must have a timeout.

Example:

```text
AI request
   ↓
Timeout
   ↓
Retry once/twice
   ↓
Fallback
```

The automation should never wait indefinitely for AI.

---

# 36. Cost Control

AI calls should be minimized.

Do not call AI repeatedly for the same lead when the result can be cached.

Example:

```text
Lead classification
    ↓
Cache result
```

Message generation should happen only when necessary.

---

# 37. Caching

Possible cached AI results:

```text
Lead Classification
Verified Context
Message Draft
Message Strategy
```

Cache should be invalidated when important lead information changes.

---

# 38. AI Loop Per Lead

The complete loop:

```text
┌──────────────────────┐
│ Load Lead            │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Check Existing State │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Understand Lead      │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Choose Strategy      │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Generate Message     │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Validate Message     │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ System Checks        │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Send                 │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Save Result          │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Observe Outcome      │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Improve Future       │
└──────────────────────┘
```

---

# 39. AI Safety Gates

Before every external message, the following gates must pass:

```text
Gate 1:
Lead is eligible

Gate 2:
Channel is available

Gate 3:
Message has not already been sent

Gate 4:
Message contains no fabricated facts

Gate 5:
Message passes validation

Gate 6:
Provider/API is configured

Gate 7:
No opt-out or stop condition exists
```

If any gate fails:

```text
DO NOT SEND
```

---

# 40. Opt-Out Protection

If a lead explicitly requests no further contact:

```text
Lead Status = OPTED_OUT
```

The system must stop automated outreach to that lead.

Future runs must skip the lead.

This state should take priority over AI recommendations.

---

# 41. AI Decision Priority

When decisions conflict, use this hierarchy:

```text
1. Safety / system rules
2. Lead opt-out / stop conditions
3. Existing delivery state
4. Provider/API availability
5. Campaign configuration
6. Verified lead information
7. AI recommendation
8. Default fallback
```

AI is therefore an intelligence layer, not the final authority over system safety.

---

# 42. Example AI Decision

Input:

```text
Name: Prachi Lilhare
City: Nagpur
Verified professional information: Yes
Verified business information: Yes
Email: Available
WhatsApp: Available
Previous contact: None
```

AI:

```text
Lead Type:
PROFESSIONAL

Confidence:
HIGH

Strategy:
VERIFIED_PROFESSIONAL

Channels:
EMAIL + WHATSAPP

Personalization:
Name + verified professional context
```

Automation then validates the decision and executes it.

---

# 43. Example Unknown Lead

Input:

```text
Name: Sample Lead Name
City: Sample City
Email: Available
Phone: Available
Verified business: No
```

AI:

```text
Lead Type:
UNKNOWN

Confidence:
LOW

Strategy:
GENERIC

Personalization:
Name only

Channels:
EMAIL + WHATSAPP
```

The AI must not invent a business or profession.

---

# 44. Example Failed Channel

State:

```text
Email: SENT
WhatsApp: FAILED
```

Next run:

```text
AI does not regenerate the email.

Email:
SKIP

WhatsApp:
Evaluate retry
```

This preserves duplicate protection.

---

# 45. Dashboard AI Events

The dashboard may display:

```text
AI: Lead classified
AI: Personalized message generated
AI: Message validated
Email: Sent
WhatsApp: Sent
```

Example:

```text
✓ Rohit Kumar — Lead analyzed
✓ Rohit Kumar — Email generated
✓ Rohit Kumar — Email sent
✓ Rohit Kumar — WhatsApp sent
```

Do not expose internal AI prompts or private model data.

---

# 46. AI Loop Success Criteria

The AI Loop is successful when it:

```text
✓ Produces relevant messages
✓ Uses verified information
✓ Avoids fabricated personalization
✓ Avoids duplicate messages
✓ Handles unknown leads safely
✓ Improves based on real outcomes
✓ Stops when a lead replies or opts out
✓ Falls back safely when AI is unavailable
✓ Does not block the automation engine
✓ Keeps all important decisions traceable
```

---

# 47. Final Architecture Rule

The system follows:

```text
AI THINKS
      ↓
SYSTEM VALIDATES
      ↓
AUTOMATION EXECUTES
      ↓
SYSTEM RECORDS
      ↓
AI LEARNS
```

The AI should **never bypass the system validation layer**.

The final objective is not to make the AI send as many messages as possible.

The objective is:

> **Use available evidence to make each outreach decision more relevant, execute it safely, record the outcome, and use real results to improve future outreach.**