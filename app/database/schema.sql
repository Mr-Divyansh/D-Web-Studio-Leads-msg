-- D Web Studio Local Outreach Automation - SQLite Database Schema
-- Version: 1.0.0

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Core leads table
CREATE TABLE IF NOT EXISTS leads (
    id TEXT PRIMARY KEY,                       -- UUID or deterministic lead ID
    identity_key TEXT NOT NULL UNIQUE,         -- Normalized composite key for deduplication
    name TEXT NOT NULL,
    email TEXT,                                -- Lowercased; NULL if not available
    email_raw TEXT,
    phone TEXT,                                -- Normalized 10-digit number
    phone_raw TEXT,
    is_priority INTEGER NOT NULL DEFAULT 0,    -- 1 if Priority, 0 otherwise
    gender TEXT,                               -- 'm', 'f', or NULL
    age INTEGER,
    city TEXT,
    education TEXT,
    source TEXT DEFAULT 'Apna',
    unverified_notes TEXT,                     -- Undocumented Column H notes (treated as UNVERIFIED)
    
    -- Channel statuses (denormalized for fast queries)
    email_status TEXT NOT NULL DEFAULT 'PENDING',       -- PENDING, SENT, FAILED, NOT_AVAILABLE
    whatsapp_status TEXT NOT NULL DEFAULT 'PENDING',    -- PENDING, SENT, FAILED, NOT_AVAILABLE, UNKNOWN
    overall_status TEXT NOT NULL DEFAULT 'PENDING',     -- PENDING, PROCESSING, COMPLETED, FAILED, SKIPPED, NOT_MATCH
    
    is_opted_out INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_leads_priority ON leads(is_priority);
CREATE INDEX IF NOT EXISTS idx_leads_overall_status ON leads(overall_status);
CREATE INDEX IF NOT EXISTS idx_leads_email_status ON leads(email_status);
CREATE INDEX IF NOT EXISTS idx_leads_whatsapp_status ON leads(whatsapp_status);

-- Outreach delivery history (one record per channel attempt)
CREATE TABLE IF NOT EXISTS outreach (
    id TEXT PRIMARY KEY,
    lead_id TEXT NOT NULL,
    channel TEXT NOT NULL,                     -- 'email' or 'whatsapp'
    status TEXT NOT NULL,                      -- SENT, FAILED, UNKNOWN
    provider TEXT NOT NULL,                    -- 'gmail', 'meta_cloud', 'stub'
    provider_message_id TEXT,
    template_version TEXT,
    subject TEXT,
    message_body TEXT,
    error_message TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 1,
    run_id TEXT,
    sent_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE,
    CONSTRAINT uq_outreach_lead_channel UNIQUE (lead_id, channel)
);

CREATE INDEX IF NOT EXISTS idx_outreach_lead ON outreach(lead_id);
CREATE INDEX IF NOT EXISTS idx_outreach_channel ON outreach(channel);
CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach(status);

-- Automation run tracking
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'RUNNING',    -- READY, RUNNING, PAUSED, STOPPED, COMPLETE, ERROR
    mode TEXT NOT NULL DEFAULT 'DRY RUN',      -- DRY RUN, LIVE
    total_leads INTEGER NOT NULL DEFAULT 0,
    completed_leads INTEGER NOT NULL DEFAULT 0,
    pending_leads INTEGER NOT NULL DEFAULT 0,
    failed_leads INTEGER NOT NULL DEFAULT 0,
    current_lead_id TEXT,
    current_lead_name TEXT,
    current_action TEXT,
    error_message TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME
);

-- Operational activity events
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    lead_id TEXT,
    lead_name TEXT,
    event_type TEXT NOT NULL,                  -- AUTOMATION_STARTED, EMAIL_SENT, WHATSAPP_SENT, etc.
    channel TEXT,
    status TEXT,                               -- SUCCESS, FAILED, INFO, WARNING
    message TEXT NOT NULL,
    icon TEXT DEFAULT '•',                     -- ✓, →, ○, •, ✕, ?
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);

-- Outreach message templates
CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,                     -- 'email' or 'whatsapp'
    version TEXT NOT NULL,                     -- 'v1', 'v2', etc.
    lead_type TEXT NOT NULL DEFAULT 'GENERIC', -- BUSINESS_OWNER, PROFESSIONAL, GENERIC
    subject_template TEXT,
    body_template TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- External service connections
CREATE TABLE IF NOT EXISTS connections (
    id TEXT PRIMARY KEY,
    service TEXT NOT NULL UNIQUE,              -- 'gmail', 'whatsapp', 'ai'
    provider TEXT NOT NULL,                    -- 'gmail_oauth', 'meta_cloud', 'stub', 'openai'
    status TEXT NOT NULL DEFAULT 'DISCONNECTED',-- CONNECTED, DISCONNECTED, ERROR
    account_identifier TEXT,                   -- Email address, Phone number, or Model name
    phone_number_id TEXT,
    business_account_id TEXT,
    last_tested_at DATETIME,
    error_message TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Opt-out registry
CREATE TABLE IF NOT EXISTS opt_outs (
    id TEXT PRIMARY KEY,
    lead_id TEXT,
    identifier TEXT NOT NULL UNIQUE,           -- Email address or normalized phone number
    channel TEXT NOT NULL,                     -- 'email', 'whatsapp', 'all'
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Lead replies
CREATE TABLE IF NOT EXISTS replies (
    id TEXT PRIMARY KEY,
    lead_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    content TEXT NOT NULL,
    classification TEXT NOT NULL DEFAULT 'UNKNOWN', -- INTERESTED, QUESTION, NOT_NOW, NOT_INTERESTED, OPT_OUT, UNKNOWN
    requires_human_handoff INTEGER NOT NULL DEFAULT 0,
    received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- AI decisions log
CREATE TABLE IF NOT EXISTS ai_decisions (
    id TEXT PRIMARY KEY,
    lead_id TEXT NOT NULL,
    lead_category TEXT NOT NULL,               -- BUSINESS_OWNER, PROFESSIONAL, UNKNOWN
    confidence REAL NOT NULL DEFAULT 0.0,
    strategy TEXT NOT NULL,
    recommended_channels TEXT NOT NULL,        -- 'email', 'whatsapp', 'both'
    verified_facts TEXT,                       -- JSON string of verified facts
    rationale TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
);