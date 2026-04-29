import os
import uuid
import base64
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import smtplib

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

GMAIL_SENDER    = os.getenv("GMAIL_SENDER_EMAIL")
TOKEN_PATH      = os.getenv("GMAIL_TOKEN_PATH", "gmail_token.json")
CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "").replace("\xa0", "").strip()

def _get_gmail_service():
    """Build authenticated Gmail API service."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    print("=== DEBUG GMAIL ===")
    print("TOKEN_PATH:", TOKEN_PATH)
    print("TOKEN EXISTS:", os.path.exists(TOKEN_PATH))
    print("CREDS_PATH:", CREDENTIALS_PATH)
    print("CREDS EXISTS:", os.path.exists(CREDENTIALS_PATH))
    print("===================")

    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # Auto-refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    if not creds or not creds.valid:
        raise ValueError(
            f"Gmail credentials not valid. Run generate_token.py first. "
            f"Token path: {TOKEN_PATH}"
        )

    return build('gmail', 'v1', credentials=creds)


def _get_engine():
    from grievance_ai_agent.tools.db_tools import engine
    return engine


def _ensure_table():
    from sqlalchemy import text
    with _get_engine().connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sent_emails (
                id        TEXT PRIMARY KEY,
                to_email  TEXT,
                authority TEXT,
                subject   TEXT,
                body      TEXT,
                sent_at   TIMESTAMP DEFAULT NOW(),
                status    TEXT DEFAULT 'sent',
                gmail_id  TEXT
            )
        """))
        conn.commit()


def _build_email_body(
    authority_name: str,
    to_email: str,
    issue_summary: str,
    location: str,
    sla_days: int,
    reference_id: str
) -> str:
    today = datetime.now().strftime("%d %B %Y")

    clean_issue = issue_summary.strip()
    if len(clean_issue) > 200 or clean_issue.lower().startswith('to,'):
        lines = [l.strip() for l in clean_issue.split('\n') if l.strip()]
        for line in lines:
            if line.lower().startswith('subject:'):
                clean_issue = line.replace('Subject:', '').replace('subject:', '').strip()
                break
        else:
            clean_issue = next(
                (l for l in lines if not l.startswith(('To,', 'The ', 'Subject:', 'Respected'))),
                lines[0] if lines else issue_summary
            )[:200]

    return f"""To,
The {authority_name},

Subject: Formal Grievance Complaint - {clean_issue}

Respected Sir/Madam,

I am writing to formally register my grievance regarding the following issue:

Issue: {clean_issue}
Location: {location}
Reference ID: {reference_id}
Date: {today}

This matter falls under your jurisdiction. As per the Consumer Protection Act,
2019 (Section 2(42)) and the relevant Service Level Agreement, I request prompt
resolution within {sla_days} days of receipt of this complaint.

If this matter remains unresolved beyond the SLA period, I reserve the right to
escalate this to the appropriate higher authority, the Consumer Disputes Redressal
Commission, and relevant regulatory bodies.

I trust you will take immediate action on this matter.

Yours sincerely,
Citizen (via GrievanceOS — Automated Grievance Resolution System)
Date: {today}

---
This complaint was filed and tracked via GrievanceOS.
Reference: #{reference_id}
"""

def _build_escalation_body(
    authority_name: str,
    grievance_id: str,
    original_issue: str,
    days_overdue: int,
    original_authority: str
) -> str:
    today = datetime.now().strftime("%d %B %Y")
    return f"""To,
The {authority_name},

Subject: ESCALATION - Unresolved Grievance Reference #{grievance_id[:8].upper()}

Respected Sir/Madam,

This is a formal escalation notice regarding a grievance that has remained 
unresolved beyond its mandated SLA period.

Grievance Reference: {grievance_id[:8].upper()}
Original Issue: {original_issue}
Filed with: {original_authority}
Days Overdue: {days_overdue} days past SLA deadline
Date of Escalation: {today}

Despite filing a formal complaint through the appropriate channel, no resolution 
has been provided within the stipulated timeframe.

Under Section 2(42) of the Consumer Protection Act, 2019, this constitutes a 
deficiency in service. We request your immediate intervention and resolution 
within 48 hours, failing which this matter will be referred to the Consumer 
Disputes Redressal Commission.

Yours sincerely,
GrievanceOS Auto-Escalation Engine
Date: {today}

---
Automated escalation via GrievanceOS.
Reference: #{grievance_id[:8].upper()}
"""


def _send_via_gmail_api(
    to_email: str,
    subject: str,
    body: str
) -> str:
    """
    Send email using Gmail API. Returns Gmail message ID.
    Falls back gracefully if Gmail API fails.
    """
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"SMTP: Email sent to {to_email}")
        return "smtp_sent"

    except Exception as e:
        import traceback
        print("SMTP ERROR:")
        print(traceback.format_exc())
        return ""


def _store_email(
    email_id: str,
    to_email: str,
    authority: str,
    subject: str,
    body: str,
    status: str,
    gmail_id: str = ""
):
    """Store email record in AlloyDB."""
    try:
        _ensure_table()
        from sqlalchemy import text
        with _get_engine().connect() as conn:
            conn.execute(text("""
                INSERT INTO sent_emails
                  (id, to_email, authority, subject, body, status, gmail_id)
                VALUES (:id, :to, :auth, :sub, :body, :status, :gmail_id)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id":       email_id,
                "to":       to_email,
                "auth":     authority,
                "sub":      subject,
                "body":     body,
                "status":   status,
                "gmail_id": gmail_id
            })
            conn.commit()
        print(f"Email stored: #{email_id} | gmail_id={gmail_id}")
    except Exception as e:
        print(f"Email storage error: {e}")


def send_grievance_email(
    to_email: str,
    authority_name: str,
    subject: str,
    complaint_text: str,
    location: str = "India",
    sla_days: int = 7
) -> dict:
    email_id = str(uuid.uuid4())[:8].upper()

    body = _build_email_body(
        authority_name = authority_name,
        to_email       = to_email,
        issue_summary  = complaint_text,
        location       = location,
        sla_days       = sla_days,
        reference_id   = email_id
    )

    gmail_id   = _send_via_gmail_api(to_email, subject, body)
    gmail_sent = bool(gmail_id)

    _store_email(
        email_id  = email_id,
        to_email  = to_email,
        authority = authority_name,
        subject   = subject,
        body      = body,
        status    = "sent",
        gmail_id  = gmail_id
    )

    return {
        "status":     "sent",
        "email_id":   email_id,
        "gmail_sent": gmail_sent,
        "gmail_id":   gmail_id,
        "message":    f"Email {'sent via Gmail' if gmail_sent else 'logged'} to {authority_name} at {to_email}",
        "recipient":  to_email,
        "subject":    subject,
        "preview":    body[:400]
    }

def send_escalation_email(
    to_email: str,
    authority_name: str,
    grievance_id: str,
    original_issue: str,
    days_overdue: int,
    original_authority: str = "Previous Authority"
) -> dict:
    """
    Sends escalation email via Gmail API.

    Args:
        to_email: Escalation authority email
        authority_name: Name of escalation authority
        grievance_id: Original grievance reference ID
        original_issue: Description of the original issue
        days_overdue: Number of days past SLA deadline
        original_authority: Name of the original authority

    Returns:
        status, email_id, message, gmail_sent
    """
    email_id = str(uuid.uuid4())[:8].upper()
    subject  = f"ESCALATION: Unresolved Grievance #{grievance_id[:8].upper()}"

    body = _build_escalation_body(
        authority_name     = authority_name,
        grievance_id       = grievance_id,
        original_issue     = original_issue,
        days_overdue       = days_overdue,
        original_authority = original_authority
    )

    gmail_id   = _send_via_gmail_api(to_email, subject, body)
    gmail_sent = bool(gmail_id)

    _store_email(
        email_id  = email_id,
        to_email  = to_email,
        authority = authority_name,
        subject   = subject,
        body      = body,
        status    = "escalation",
        gmail_id  = gmail_id
    )

    return {
        "status":     "sent",
        "email_id":   email_id,
        "gmail_sent": gmail_sent,
        "gmail_id":   gmail_id,
        "message":    f"Escalation email {'sent via Gmail' if gmail_sent else 'logged'} to {authority_name}",
        "recipient":  to_email
    }
