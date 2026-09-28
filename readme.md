# D Web Studio — Outreach Automation Dashboard

A local-first outreach automation system for managing leads and sending controlled Email and WhatsApp outreach through official APIs.

The system is designed to:

```text
Import Leads
    ↓
Store Local State
    ↓
Filter Eligible Leads
    ↓
Generate Outreach
    ↓
Send Email / WhatsApp
    ↓
Record Results
    ↓
Resume Safely
    ↓
Track Progress
```

---

# 1. Project Goal

The goal of this project is to create a simple local control center for D Web Studio's lead outreach.

The system should allow the user to:

* Import leads from Excel.
* Filter priority leads.
* Store leads locally.
* Send Email through Gmail API.
* Send WhatsApp messages through a configured WhatsApp API.
* Track every delivery result.
* Prevent duplicate messages.
* Resume after interruption.
* Keep an activity log.
* Use AI for personalization and decision support.
* Keep the dashboard local.

The project is intentionally **not** designed to become a complex CRM or public SaaS platform.

---

# 2. Core Principle

The system follows:

```text
AI THINKS
    ↓
SYSTEM VALIDATES
    ↓
AUTOMATION EXECUTES
    ↓
DATABASE RECORDS
    ↓
MEMORY PERSISTS
    ↓
AI LEARNS
```

AI is an intelligence layer.

The deterministic automation engine remains responsible for execution and state management.

---

# 3. Features

## Lead Management

* Excel import.
* Lead normalization.
* Duplicate detection.
* Priority filtering.
* Local SQLite storage.
* Stable lead IDs.
* Lead validation.

## Email

* Gmail API integration.
* Google OAuth authentication.
* Personalized message generation.
* Delivery status tracking.
* Message ID tracking.
* Error handling.
* Duplicate protection.

## WhatsApp

* Configurable WhatsApp API/provider.
* Phone normalization.
* Availability handling.
* Message status tracking.
* Provider message ID tracking.
* Duplicate protection.
* Unknown availability state.

## Automation

* Sequential lead processing.
* Background execution.
* Resume after interruption.
* Partial completion handling.
* Error isolation.
* Retry handling.
* Rate limiting.
* Run IDs.

## Dashboard

* Total leads.
* Completed leads.
* Pending leads.
* Failed leads.
* Current lead.
* Current action.
* Progress.
* Activity log.
* Start/stop controls.
* Run status.
* Completion state.

## AI

* Lead classification.
* Message personalization.
* Channel recommendations.
* Message quality checking.
* Reply classification.
* Template improvement.
* Evidence-aware personalization.

---

# 4. Important Safety Features

The system is designed around several non-negotiable rules.

### No accidental duplicates

If:

```text
Email = SENT
```

the system does not send that email again.

### Resume support

If:

```text
Email = SENT
WhatsApp = PENDING
```

a restart processes only WhatsApp.

### No fabricated personalization

AI must not invent:

* Companies.
* Jobs.
* Businesses.
* Achievements.
* Websites.
* Relationships.
* Previous conversations.

### Opt-out protection

If a recipient explicitly opts out, future automated outreach must be skipped.

### Unknown state

When the system cannot confidently determine a result:

```text
UNKNOWN
```

is used instead of guessing.

### Secret protection

API keys, OAuth credentials and tokens must never be committed to Git.

---

# 5. Architecture

```text
                    ┌─────────────────────┐
                    │      Excel File     │
                    │      leads.xlsx     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Lead Importer    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       SQLite        │
                    │   outreach.db       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Automation Engine  │
                    └───────┬─────┬───────┘
                            │     │
                 ┌──────────┘     └──────────┐
                 ▼                           ▼
        ┌─────────────────┐        ┌─────────────────┐
        │    Gmail API    │        │  WhatsApp API   │
        └────────┬────────┘        └────────┬────────┘
                 │                           │
                 └──────────┬────────────────┘
                            ▼
                    ┌─────────────────────┐
                    │   Result / Memory   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Dashboard       │
                    └─────────────────────┘
```

---

# 6. Project Structure

```text
d-web-studio-outreach/
│
├── app/
│   ├── main
│   │
│   ├── dashboard/
│   │   ├── components/
│   │   ├── pages/
│   │   └── state/
│   │
│   ├── automation/
│   │   ├── engine
│   │   ├── queue
│   │   ├── processor
│   │   └── scheduler
│   │
│   ├── leads/
│   │   ├── importer
│   │   ├── repository
│   │   ├── validator
│   │   └── filter
│   │
│   ├── messaging/
│   │   ├── templates
│   │   ├── personalization
│   │   └── message_builder
│   │
│   ├── integrations/
│   │   ├── gmail/
│   │   └── whatsapp/
│   │
│   ├── database/
│   │   ├── models
│   │   ├── migrations
│   │   └── connection
│   │
│   ├── logging/
│   │   └── logger
│   │
│   └── config/
│       └── settings
│
├── data/
│   ├── leads.xlsx
│   ├── outreach.db
│   └── logs/
│
├── credentials/
│   └── gmail/
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

# 7. Technology Direction

The exact framework can be selected during implementation, but the architecture should remain:

```text
Local Application
        +
SQLite
        +
Excel
        +
Gmail API
        +
WhatsApp API
        +
Optional AI API
```

The application should be easy to run locally from the user's computer.

---

# 8. Data Flow

## Import

```text
leads.xlsx
    ↓
Validate
    ↓
Normalize
    ↓
Deduplicate
    ↓
SQLite
```

## Outreach

```text
SQLite
    ↓
Find eligible lead
    ↓
Check previous state
    ↓
Build message
    ↓
Validate message
    ↓
Send
    ↓
Save result
```

## Resume

```text
Application stopped
       ↓
Application restarted
       ↓
Load SQLite
       ↓
Find unfinished work
       ↓
Skip completed actions
       ↓
Resume remaining actions
```

---

# 9. Lead Fields

The initial lead dataset may contain:

```text
Name
Email
Phone
Priority
Gender
Age
City/State
Education/Degree
Source
```

Runtime fields should additionally track:

```text
Lead ID
Email Status
WhatsApp Status
Lead Status
Last Contacted At
Email Message ID
WhatsApp Message ID
Run ID
Error
Opt-Out
Created At
Updated At
```

---

# 10. Status System

## Email

```text
PENDING
SENT
FAILED
NOT_AVAILABLE
```

## WhatsApp

```text
PENDING
SENT
FAILED
NOT_AVAILABLE
UNKNOWN
```

## Lead

```text
PENDING
PROCESSING
COMPLETED
FAILED
SKIPPED
NOT_MATCH
```

## Run

```text
READY
RUNNING
PAUSED
COMPLETE
ERROR
```

---

# 11. Environment Configuration

Configuration should be stored outside application source code.

Example:

```env
APP_ENV=local

DRY_RUN=true

EMAIL_ENABLED=true
WHATSAPP_ENABLED=true
AI_ENABLED=true

MAX_RETRIES=3

EMAIL_DELAY_SECONDS=10
WHATSAPP_DELAY_SECONDS=10

PRIORITY_ONLY=true
FOLLOW_UP_ENABLED=false
```

Actual secrets should not be included in this file when it is committed.

---

# 12. Gmail Setup

The application uses Gmail API with OAuth.

High-level process:

```text
Google Cloud Project
        ↓
OAuth Client
        ↓
credentials.json
        ↓
Local OAuth Login
        ↓
token.json
        ↓
Gmail API
```

Credentials should be stored locally.

Recommended location:

```text
credentials/gmail/
```

Do not commit:

```text
credentials.json
token.json
```

to Git.

---

# 13. WhatsApp Setup

The application requires a WhatsApp Business/API provider that supports programmatic messaging.

The provider configuration should be stored securely.

The system must not assume that a normal personal WhatsApp account automatically provides API access.

The WhatsApp adapter should hide provider-specific implementation from the rest of the application.

Conceptually:

```text
Automation Engine
       ↓
WhatsApp Adapter
       ↓
Configured Provider/API
```

This allows the provider to be changed later without rewriting the automation engine.

---

# 14. AI Integration

AI is optional.

The application should continue operating safely if AI is disabled or unavailable.

AI can be used for:

```text
Lead classification
Message personalization
Message generation
Quality checking
Reply classification
Template analysis
```

AI cannot override:

```text
Duplicate protection
Opt-out
Campaign scope
Provider state
System safety rules
Database state
```

---

# 15. Dry Run

Before sending real messages, enable:

```env
DRY_RUN=true
```

In this mode the system should:

```text
Load leads
    ↓
Select leads
    ↓
Generate messages
    ↓
Validate messages
    ↓
Simulate delivery
    ↓
Show results
```

No real message should be sent.

After testing:

```env
DRY_RUN=false
```

should explicitly enable live sending.

The dashboard should clearly indicate the current mode.

---

# 16. Running the Application

The exact commands depend on the selected implementation framework.

The intended workflow is:

```text
1. Install dependencies.
2. Configure environment.
3. Configure Gmail OAuth.
4. Configure WhatsApp API.
5. Import leads.
6. Run dry mode.
7. Review generated messages.
8. Start controlled live run.
```

Example development flow:

```bash
# Create environment
python -m venv .venv

# Activate environment
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start application
python -m app.main
```

These commands may be adjusted when the final application framework is selected.

---

# 17. First Run

The first run should be small and controlled.

Recommended:

```text
1 lead
    ↓
Verify
    ↓
Small batch
    ↓
Verify
    ↓
Larger batch
```

Do not immediately run the entire database through live outreach.

---

# 18. Recommended Development Sequence

```text
Phase 0
Project Setup
      ↓
Phase 1
Lead Import + SQLite
      ↓
Phase 2
Dashboard
      ↓
Phase 3
Gmail
      ↓
Phase 4
WhatsApp
      ↓
Phase 5
Automation Engine
      ↓
Phase 6
AI
      ↓
Phase 7
Memory + Resume
      ↓
Phase 8
Testing
      ↓
Phase 9
Live Release
```

See `phases.md` for the detailed implementation roadmap.

---

# 19. Documentation

The project documentation is divided into focused files.

```text
README.md
    → Project overview and setup

prd.md
    → Product requirements

design.md
    → UI/UX and visual system

architecture.md
    → Technical architecture

phases.md
    → Implementation phases

ai-loop.md
    → AI decision and automation loop

memory.md
    → Persistent memory and state

rules.md
    → Non-negotiable system rules
```

These documents should be treated as the project specification.

---

# 20. Development Rules

Before implementing a feature, verify:

```text
Does it fit the architecture?
Does it preserve existing state?
Can it create duplicate sends?
Does it expose credentials?
Does it respect campaign scope?
Does it respect opt-outs?
Does it handle failure?
Can it resume after restart?
```

If a feature violates one of these requirements, fix the architecture or rule before implementing the feature.

---

# 21. Testing Checklist

Before live use:

```text
[ ] Excel import works
[ ] Duplicate detection works
[ ] Priority filtering works
[ ] SQLite persistence works
[ ] Dashboard loads
[ ] Dry-run works
[ ] Gmail OAuth works
[ ] Test email works
[ ] WhatsApp API works
[ ] Test WhatsApp message works
[ ] Duplicate protection works
[ ] Restart/resume works
[ ] Partial completion works
[ ] Error handling works
[ ] Opt-out handling works
[ ] AI fallback works
[ ] Credentials are protected
[ ] Logs contain no secrets
```

---

# 22. Operational Rules

The application must:

```text
Never send twice accidentally.
Never invent lead information.
Never ignore an opt-out.
Never assume WhatsApp availability.
Never lose persistent state.
Never expose credentials.
Never allow one failed lead to crash the campaign.
Never claim success without evidence.
Never allow AI to bypass system rules.
Never report ALL DONE while work remains.
```

When uncertain:

```text
Record UNKNOWN.
Do not guess.
```

---

# 23. Security

Sensitive files must be ignored by Git.

Example `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc

credentials/
token.json

data/outreach.db
data/logs/

*.log
```

If the lead Excel file contains private data, it should also remain outside version control.

---

# 24. Privacy

The application should collect and retain only information necessary for the outreach workflow.

Avoid unnecessary storage of sensitive personal information.

The system should minimize:

```text
Collection
Storage
Transmission
Logging
```

---

# 25. Troubleshooting

## Gmail authentication fails

Check:

```text
OAuth client configuration
credentials.json
Google account authorization
token.json
Gmail API access
```

Do not paste credentials into source code.

---

## WhatsApp fails

Check:

```text
Provider credentials
Phone normalization
Provider account status
API response
Message/template requirements
Rate limits
```

If availability cannot be confirmed, use:

```text
UNKNOWN
```

rather than guessing.

---

## Duplicate message risk

Stop the run and inspect:

```text
outreach.db
```

Verify:

```text
Email Status
WhatsApp Status
Message ID
Run ID
```

Do not blindly rerun the campaign.

---

## Application crashes

Restart the application.

The system should load persistent state and continue from the last safe state.

---

# 26. Expected Dashboard

```text
┌──────────────────────────────────────────────────────┐
│ D WEB STUDIO                              ● READY     │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Total       Completed       Pending       Failed      │
│  70            12              58            0        │
│                                                      │
│             [ START AUTOMATION ]                     │
│                                                      │
│ CURRENT ACTIVITY                                     │
│ Rohit Kumar                                          │
│ Sending Email…                                       │
│ ████████████░░░░░░░░  12 / 70                       │
│                                                      │
│ ACTIVITY                                             │
│ ✓ Prachi Lilhare — Email sent                       │
│ ✓ Prachi Lilhare — WhatsApp sent                    │
│ • Pintu — WhatsApp unavailable                      │
│ → Rohit Kumar — Sending email…                      │
│ ○ Next lead — Pending                                │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

# 27. Definition of Done

The first production-ready version is complete when:

```text
[✓] Leads import successfully
[✓] Leads persist locally
[✓] Priority filtering works
[✓] Dashboard displays real state
[✓] Gmail integration works
[✓] WhatsApp integration works
[✓] Messages are generated correctly
[✓] Messages are delivered through configured APIs
[✓] Results are persisted
[✓] Duplicate sending is prevented
[✓] Interrupted runs resume
[✓] Errors are isolated
[✓] Opt-outs are respected
[✓] Dry-run works
[✓] Credentials are protected
[✓] AI cannot bypass system rules
[✓] Activity logs work
[✓] Full controlled test succeeds
```

---

# 28. Project Philosophy

This project is intentionally simple.

It should not become a complicated CRM.

The objective is:

```text
LOAD
 ↓
UNDERSTAND
 ↓
VALIDATE
 ↓
MESSAGE
 ↓
SEND
 ↓
RECORD
 ↓
RESUME
 ↓
IMPROVE
```

Every additional feature should justify its complexity.

The system should prefer:

```text
Simple + Reliable
```

over:

```text
Complex + Fragile
```

---

# 29. Final Architecture Principle

The complete system is:

```text
              ┌──────────────┐
              │    LEADS     │
              └──────┬───────┘
                     ↓
              ┌──────────────┐
              │   DATABASE   │
              └──────┬───────┘
                     ↓
              ┌──────────────┐
              │      AI      │
              │ Intelligence │
              └──────┬───────┘
                     ↓
              ┌──────────────┐
              │   VALIDATOR  │
              └──────┬───────┘
                     ↓
              ┌──────────────┐
              │ AUTOMATION   │
              │    ENGINE    │
              └──────┬───────┘
                  ┌───┴───┐
                  ↓       ↓
             ┌────────┐ ┌──────────┐
             │ Gmail  │ │ WhatsApp │
             └───┬────┘ └────┬─────┘
                 │            │
                 └─────┬──────┘
                       ↓
                ┌──────────────┐
                │    MEMORY    │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │  DASHBOARD   │
                └──────────────┘
```

The system's central loop is:

```text
AI THINKS
    ↓
SYSTEM VALIDATES
    ↓
AUTOMATION EXECUTES
    ↓
RESULT IS RECORDED
    ↓
MEMORY PERSISTS
    ↓
NEXT ACTION
```

This README is the starting point for developers and AI agents working on the project.
