CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS google_ml_integration;

CREATE TABLE grievances (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_input       TEXT NOT NULL,
    category         TEXT,
    location         TEXT,
    issue_summary    TEXT,
    status           TEXT DEFAULT 'filed'
                     CHECK (status IN ('filed','pending','escalated','resolved')),
    sla_deadline     DATE,
    escalation_level INT DEFAULT 0,
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE departments (
    id                         SERIAL PRIMARY KEY,
    category                   TEXT NOT NULL,
    city                       TEXT NOT NULL,
    authority_name             TEXT NOT NULL,
    email                      TEXT NOT NULL,
    sla_days                   INT NOT NULL,
    escalation_authority_email TEXT NOT NULL
);

CREATE TABLE escalations (
    id             SERIAL PRIMARY KEY,
    level          INT NOT NULL,
    authority_name TEXT NOT NULL,
    email          TEXT NOT NULL,
    sla_days       INT NOT NULL
);

CREATE TABLE precedents (
    id             SERIAL PRIMARY KEY,
    category       TEXT,
    location       TEXT,
    issue_summary  TEXT,
    resolution     TEXT,
    days_taken     INT,
    embedding      VECTOR(768)
);

CREATE TABLE workflow_logs (
    id           SERIAL PRIMARY KEY,
    grievance_id UUID REFERENCES grievances(id),
    agent_name   TEXT NOT NULL,
    action       TEXT NOT NULL,
    reasoning    TEXT,
    input_data   JSONB,
    output_data  JSONB,
    timestamp    TIMESTAMP DEFAULT NOW()
);