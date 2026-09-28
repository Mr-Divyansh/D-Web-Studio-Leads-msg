# D Web Studio — Local Outreach Automation

## System Architecture

---

# 1. Architecture Overview

The application is a **local-first outreach automation system**.

Its primary purpose is to:

1. Read leads from Excel.
2. Store and manage lead state locally.
3. Filter eligible leads.
4. Generate personalized outreach messages.
5. Send emails through Gmail API.
6. Send WhatsApp messages through the configured WhatsApp API.
7. Record the result of every action.
8. Prevent duplicate messages.
9. Resume safely after interruption.
10. Display live automation progress in the local dashboard.

The system should remain simple and modular.

```text
                    ┌──────────────────────┐
                    │      Excel File      │
                    │   Lead for web dg    │
                    │        .xlsx         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Import / Sync     │
                    │       Layer          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Local Lead Store   │
                    │   SQLite / Local DB  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Automation Engine   │
                    │                      │
                    │ Filter → Process →   │
                    │ Send → Save Status   │
                    └───────┬───────┬──────┘
                            │       │
                  ┌─────────┘       └─────────┐
                  ▼                           ▼
        ┌──────────────────┐       ┌──────────────────┐
        │    Gmail API     │       │  WhatsApp API    │
        │      Email       │       │    Messaging     │
        └────────┬─────────┘       └────────┬─────────┘
                 │                          │
                 └────────────┬─────────────┘
                              ▼
                    ┌──────────────────────┐
                    │   Status / Logs      │
                    │      Local DB        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Local Dashboard    │
                    │   Live Progress UI   │
                    └──────────────────────┘
```

---

# 2. Core Architecture Principles

## Local First

Lead data and automation state should remain on the user's computer.

Do not build a public cloud CRM for the MVP.

The local application should own:

* Lead records
* Lead statuses
* Email statuses
* WhatsApp statuses
* Processing state
* Activity logs
* Message history
* Retry information

External services are used only when required for actual delivery.

---

# 3. External Services

The system has two primary external integrations.

## Gmail API

Used for sending email.

```text
Application
    ↓
Google OAuth
    ↓
Gmail API
    ↓
Recipient
```

Authentication should use OAuth.

Never store the user's Gmail password.

Never place OAuth secrets inside the Excel file.

---

## WhatsApp API

Used for sending WhatsApp messages.

```text
Application
    ↓
Configured WhatsApp API
    ↓
WhatsApp Business/API Provider
    ↓
Recipient
```

The WhatsApp integration must be implemented behind an internal adapter so the rest of the application does not depend directly on one provider.

---

# 4. Application Layers

The application should be separated into logical layers.

```text
┌───────────────────────────────┐
│           UI Layer            │
│       Local Dashboard         │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│       Application Layer       │
│     Automation Controller     │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│        Service Layer          │
│ Lead / Email / WhatsApp       │
│ Message / Status / Logging    │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│       Data Access Layer       │
│     SQLite / Excel Sync       │
└───────────────┬───────────────┘
                │
┌───────────────────────────────┐
│       External Adapters       │
│ Gmail API / WhatsApp API      │
└───────────────────────────────┘
```

---

# 5. Recommended Project Structure

A clean project structure should be used.

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

The exact framework/language can change, but the separation of responsibilities should remain.

---

# 6. Main Components

## 6.1 Dashboard

Responsible only for:

* Showing system state
* Starting automation
* Showing progress
* Showing current lead
* Showing activity
* Showing errors
* Showing completion

The dashboard should not contain the actual email/WhatsApp sending logic.

---

# 7. Automation Engine

The Automation Engine is the core of the application.

Its responsibility is to process eligible leads safely.

Basic flow:

```text
START
  ↓
Load configuration
  ↓
Load leads
  ↓
Filter eligible leads
  ↓
For each lead
  ↓
Check existing statuses
  ↓
Process Email
  ↓
Process WhatsApp
  ↓
Update local state
  ↓
Update dashboard
  ↓
Next lead
  ↓
ALL DONE
```

---

# 8. Lead Eligibility

Before processing a lead, the engine should determine whether the lead is eligible.

Example conditions:

```text
Priority = TRUE
AND
Lead Status != COMPLETED
```

Additional checks:

```text
Email available?
Phone available?
Already contacted?
Previously failed?
Explicitly skipped?
```

The exact filtering rules should be configurable.

---

# 9. Priority Leads

The system should support priority filtering.

Example:

```text
Priority = YES
```

Only eligible priority leads should be processed when the automation is configured for priority mode.

Future versions may support:

```text
ALL
PRIORITY ONLY
MANUAL SELECTION
```

The MVP can use:

```text
PRIORITY ONLY
```

---

# 10. Duplicate Protection

Duplicate sending is one of the most important safety requirements.

Before sending email:

```text
IF Email Status == SENT
    SKIP EMAIL
```

Before sending WhatsApp:

```text
IF WhatsApp Status == SENT
    SKIP WHATSAPP
```

Example:

```text
Lead:
Rohit Kumar

Email:
SENT

WhatsApp:
PENDING
```

On the next run:

```text
Email → SKIP
WhatsApp → PROCESS
```

The system must never resend a successfully completed channel merely because the application was restarted.

---

# 11. Resume After Interruption

The application must support safe resume.

Example:

```text
Lead 1 → Completed
Lead 2 → Completed
Lead 3 → Email Sent
Lead 3 → WhatsApp Pending
Application stopped
```

After restarting:

```text
Lead 1 → Skip
Lead 2 → Skip
Lead 3 Email → Skip
Lead 3 WhatsApp → Continue
```

This makes the system resilient to:

* Computer restart
* Application crash
* API timeout
* Internet interruption
* Manual stop

---

# 12. Lead State Machine

Each lead should move through predictable states.

```text
PENDING
   │
   ▼
PROCESSING
   │
   ├───────────────┐
   ▼               ▼
COMPLETED        FAILED
   │
   ▼
   END
```

A lead may also become:

```text
SKIPPED
NOT_MATCH
```

---

# 13. Channel State Machine

Each communication channel has its own state.

## Email

```text
PENDING
   │
   ├──► SENT
   │
   └──► FAILED
```

If no email exists:

```text
NOT_AVAILABLE
```

## WhatsApp

```text
PENDING
   │
   ├──► SENT
   │
   └──► FAILED
```

If no phone exists:

```text
NOT_AVAILABLE
```

If availability cannot be reliably confirmed:

```text
UNKNOWN
```

---

# 14. Message Generation

Message generation should be separated from message delivery.

```text
Lead Data
   ↓
Message Builder
   ↓
Personalized Message
   ↓
Email Adapter / WhatsApp Adapter
```

Example personalization:

```text
{{name}}
```

becomes:

```text
Rohit
```

The message builder should not send messages itself.

---

# 15. Personalization Rules

Personalization should use verified lead data only.

Example:

```text
Hi {{name}},
```

becomes:

```text
Hi Rohit,
```

Do not automatically invent:

* Company names
* Job titles
* Businesses
* Websites
* Services
* Personal interests

If business information has not been verified, use a generic message.

---

# 16. Email Architecture

The email service should expose a simple internal interface.

Conceptually:

```text
send_email(
    recipient,
    subject,
    body
)
```

The rest of the application should not need to know Gmail API implementation details.

Architecture:

```text
Automation Engine
       ↓
Email Service
       ↓
Gmail Adapter
       ↓
Gmail API
```

---

# 17. Gmail Authentication

Authentication should use OAuth.

Conceptually:

```text
First Run
   ↓
Open Google OAuth
   ↓
User grants permission
   ↓
Local token created
   ↓
Future runs reuse token
```

Sensitive authentication files must never be committed to Git.

Example:

```text
credentials.json
token.json
.env
```

must be protected by `.gitignore`.

---

# 18. WhatsApp Architecture

WhatsApp should also use an adapter.

```text
Automation Engine
       ↓
WhatsApp Service
       ↓
WhatsApp Provider Adapter
       ↓
WhatsApp API
```

This allows the provider to be changed later without rewriting the automation engine.

---

# 19. WhatsApp Availability

The application should not assume that every phone number has WhatsApp.

Possible states:

```text
AVAILABLE
NOT_AVAILABLE
UNKNOWN
```

If the provider gives a confirmed result:

```text
AVAILABLE
```

If no valid number exists:

```text
NOT_AVAILABLE
```

If the provider cannot confirm:

```text
UNKNOWN
```

The system should never fabricate availability.

---

# 20. Database

SQLite is recommended for the local MVP.

Why:

* Local
* Lightweight
* No server required
* Easy backup
* Supports transactions
* Handles hundreds/thousands of leads easily
* Good fit for a single-user local application

Example:

```text
data/outreach.db
```

---

# 21. Lead Database Model

Recommended fields:

```text
id
name
email
phone
priority
gender
age
city
education
source

email_status
whatsapp_status
lead_status

last_contacted_at
email_message_id
whatsapp_message_id

last_error
created_at
updated_at
```

Additional fields can be added later.

---

# 22. Excel Integration

Excel should remain the user's source/import file.

Example:

```text
Lead for web dg.xlsx
```

The importer reads the Excel file and synchronizes it with the local database.

Recommended flow:

```text
Excel
  ↓
Validate columns
  ↓
Normalize data
  ↓
Insert/update local DB
  ↓
Automation Engine
```

The application should not repeatedly parse the entire Excel file during every individual lead operation.

---

# 23. Excel Status Synchronization

After processing, statuses may be written back to Excel.

Recommended columns:

```text
Email Status
WhatsApp Status
Lead Status
Last Contacted At
```

Optional:

```text
Email Message ID
WhatsApp Message ID
Last Error
```

The database should remain the primary runtime state.

Excel should act as:

```text
Input + Human-readable export
```

rather than the application's high-frequency transactional database.

---

# 24. Database as Source of Truth

During automation:

```text
Local DB = Source of Truth
```

Excel:

```text
Import / Export
```

This prevents performance problems and reduces the chance of corrupting the workbook during every API operation.

---

# 25. Transaction Safety

Important state changes should be saved immediately.

Example:

```text
Email successfully sent
       ↓
Save Email Status = SENT
       ↓
Continue to WhatsApp
```

Do not wait until the entire campaign finishes before saving state.

If the computer shuts down after an email succeeds, the application should already know that the email was sent.

---

# 26. Error Handling

Errors should be isolated by lead and channel.

Example:

```text
Lead A
Email → SENT
WhatsApp → FAILED
```

This should not prevent:

```text
Lead B
Email → SENT
WhatsApp → SENT
```

from processing.

---

# 27. Retry Strategy

Retries should be limited.

Recommended:

```text
Temporary API error
       ↓
Retry
       ↓
Retry
       ↓
If still failing → FAILED
```

Do not retry indefinitely.

Possible configuration:

```text
MAX_RETRIES = 2 or 3
```

The exact value should be configurable.

---

# 28. API Timeouts

External API requests must have timeouts.

Conceptually:

```text
Request
  ↓
Wait for response
  ↓
Success → continue
Timeout → retry
Repeated failure → mark FAILED
```

The automation engine must never remain stuck forever waiting for an API.

---

# 29. Rate Limiting

The system should support configurable delays between messages.

Example configuration:

```text
EMAIL_DELAY
WHATSAPP_DELAY
```

The values should not be hard-coded into the UI.

The system should respect applicable provider limits and messaging rules.

---

# 30. Automation Controller

The controller manages the overall run.

Responsibilities:

```text
start()
stop()
pause()
resume()
process_next_lead()
get_progress()
```

MVP may only expose:

```text
START
```

Internally, however, the engine should be structured so pause/stop can be added later.

---

# 31. Background Execution

The automation engine should run separately from the dashboard UI.

```text
┌────────────────────┐
│    Dashboard UI    │
└─────────┬──────────┘
          │
          │ commands/events
          ▼
┌────────────────────┐
│ Automation Worker  │
└─────────┬──────────┘
          │
          ▼
    External APIs
```

The UI must remain responsive while automation runs.

---

# 32. Event System

The automation worker should emit events such as:

```text
AUTOMATION_STARTED
LEAD_STARTED
EMAIL_STARTED
EMAIL_SENT
EMAIL_FAILED
WHATSAPP_STARTED
WHATSAPP_SENT
WHATSAPP_FAILED
LEAD_COMPLETED
LEAD_FAILED
AUTOMATION_COMPLETED
```

The dashboard listens to these events and updates itself.

---

# 33. Activity Logging

Every important operation should generate a local log entry.

Example:

```text
2026-09-28 12:30:04
Rohit Kumar
Email
SENT
```

Another:

```text
2026-09-28 12:30:09
Rohit Kumar
WhatsApp
FAILED
Temporary API error
```

Logs should be stored locally.

---

# 34. Security

Sensitive values must never be stored in:

* Excel
* Lead records
* Activity logs
* UI
* Git repository

Sensitive values include:

```text
OAuth credentials
Access tokens
API keys
API secrets
Refresh tokens
```

Use:

```text
.env
Local secure configuration
OS credential storage where appropriate
```

---

# 35. Git Protection

`.gitignore` should include sensitive/local files.

Example:

```text
.env
credentials.json
token.json
*.db
data/
logs/
__pycache__/
node_modules/
```

The exact ignore list can be adjusted according to the implementation.

---

# 36. Configuration

Application configuration should be centralized.

Example:

```text
APP_ENV=local

DATABASE_PATH=./data/outreach.db

EXCEL_PATH=./data/leads.xlsx

EMAIL_PROVIDER=gmail

WHATSAPP_PROVIDER=...

MAX_RETRIES=3

EMAIL_DELAY=...

WHATSAPP_DELAY=...
```

Secrets should never be hard-coded.

---

# 37. Dashboard ↔ Engine Communication

The dashboard should never directly call Gmail or WhatsApp.

Correct:

```text
Dashboard
   ↓
Automation Controller
   ↓
Automation Engine
   ↓
Services
   ↓
APIs
```

Incorrect:

```text
Dashboard
   ↓
Gmail API
```

or:

```text
Dashboard
   ↓
WhatsApp API
```

This separation makes the application easier to maintain.

---

# 38. Complete Processing Flow

For every lead:

```text
1. Load next eligible lead
        ↓
2. Mark lead PROCESSING
        ↓
3. Check Email Status
        ↓
4. If Email PENDING
        ↓
5. Build personalized email
        ↓
6. Send through Gmail API
        ↓
7. Save result immediately
        ↓
8. Check WhatsApp Status
        ↓
9. If WhatsApp PENDING
        ↓
10. Validate availability
        ↓
11. Build personalized WhatsApp message
        ↓
12. Send through WhatsApp API
        ↓
13. Save result immediately
        ↓
14. Calculate Lead Status
        ↓
15. Mark lead COMPLETED / FAILED
        ↓
16. Update dashboard
        ↓
17. Move to next lead
```

---

# 39. Example Processing Scenario

Suppose:

```text
Name: Sample Lead Name
Email: sample.lead@example.com
Phone: 9000000000
Priority: YES
```

Initial state:

```text
Email: PENDING
WhatsApp: PENDING
Lead: PENDING
```

Processing:

```text
Lead → PROCESSING

Email → SENT

WhatsApp → SENT

Lead → COMPLETED
```

Dashboard:

```text
✓ Rohit Kumar — Completed
```

---

# 40. Interrupted Processing Scenario

Suppose:

```text
Email → SENT
```

Then the application crashes before WhatsApp.

Database:

```text
Email: SENT
WhatsApp: PENDING
Lead: PROCESSING
```

After restart:

```text
Email → SKIP
WhatsApp → PROCESS
```

This prevents duplicate email delivery.

---

# 41. Failed Processing Scenario

Example:

```text
Email → SENT
WhatsApp → FAILED
```

The lead should retain:

```text
Email Status: SENT
WhatsApp Status: FAILED
```

The system should not resend the email automatically on the next run.

Only the failed/pending channel should be eligible for retry.

---

# 42. Completion Logic

A lead is considered completed when every applicable channel has reached a terminal state.

Terminal states:

```text
SENT
NOT_AVAILABLE
SKIPPED
```

Example:

```text
Email: SENT
WhatsApp: NOT_AVAILABLE
```

Result:

```text
Lead: COMPLETED
```

Example:

```text
Email: SENT
WhatsApp: FAILED
```

Result:

```text
Lead: FAILED
```

---

# 43. Global Automation Completion

The entire run is complete when all eligible leads have reached terminal lead states.

Example:

```text
70 eligible leads

Completed: 68
Failed: 2
Pending: 0
```

Then:

```text
AUTOMATION COMPLETED
```

The dashboard displays:

```text
ALL DONE ✓
```

---

# 44. MVP Architecture

The first version should contain only:

```text
Excel Import
      +
SQLite
      +
Local Dashboard
      +
Automation Engine
      +
Gmail API
      +
WhatsApp API
      +
Status Tracking
      +
Activity Logs
```

Do not build these initially:

```text
Cloud CRM
User accounts
Team management
Billing
Analytics dashboard
Complex charts
AI agent marketplace
Public API
Multi-tenant architecture
```

---

# 45. Future Architecture

The architecture should allow future additions without rewriting the core.

Possible future modules:

```text
Lead Research Service
AI Message Generator
Multiple Gmail Accounts
Multiple WhatsApp Providers
Campaign Management
Lead Scoring
Advanced Scheduling
Team Accounts
Cloud Sync
Analytics
```

These should be added as separate modules rather than tightly coupling them to the existing engine.

---

# 46. Reliability Rules

The following rules are mandatory:

```text
1. Never send the same successful channel twice.
2. Save state immediately after successful delivery.
3. Never lose existing lead state during import.
4. Do not crash the entire run because one lead fails.
5. Do not expose credentials in the UI.
6. Do not assume WhatsApp availability.
7. Do not invent lead information.
8. Keep the dashboard responsive.
9. Use timeouts for external APIs.
10. Limit retries.
11. Keep runtime state local.
12. Make the system safely resumable.
```

---

# 47. Architecture Summary

The final architecture is:

```text
                     USER
                      │
                      ▼
             ┌─────────────────┐
             │ Local Dashboard │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Automation      │
             │ Controller      │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Automation      │
             │ Engine          │
             └───────┬─────────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      Lead Service  Message   Status
          │         Builder    Store
          │           │          │
          ▼           ▼          ▼
       SQLite      Email/WA    SQLite
          │
          ▼
       Excel Sync
          │
          ▼
   ┌──────┴─────────┐
   ▼                ▼
Gmail API       WhatsApp API
```

---

# 48. Final Architecture Principle

The system should follow one central rule:

> **The dashboard controls the automation, the automation engine controls the workflow, services control integrations, and the local database controls state.**

This separation keeps the application:

* Reliable
* Resumable
* Maintainable
* Local-first
* Easy to debug
* Easy to extend
* Safe from duplicate sends

The MVP should remain small and focused on one job:

> **Select eligible leads → contact them through configured channels → save every result → show the user exactly what happened.**
