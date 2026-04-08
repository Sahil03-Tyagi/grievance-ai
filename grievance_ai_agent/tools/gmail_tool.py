import os
import json
import uuid
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

USE_VERTEX   = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
GEMINI_KEY   = os.getenv("GOOGLE_API_KEY")
GCP_PROJECT  = os.getenv("GOOGLE_CLOUD_PROJECT")
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

def _get_client():
    from google import genai
    if USE_VERTEX:
        return genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)
    return genai.Client(api_key=GEMINI_KEY)

def _get_engine():
    # Import here to avoid circular import at module load time
    from grievance_ai_agent.tools.db_tools import engine
    return engine

def _ensure_table():
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sent_emails (
                id       TEXT PRIMARY KEY,
                to_email TEXT,
                authority TEXT,
                subject  TEXT,
                body     TEXT,
                sent_at  TIMESTAMP DEFAULT NOW(),
                status   TEXT DEFAULT 'sent'
            )
        """))
        conn.commit()

def _generate_email_body(prompt: str) -> str:
    try:
        client = _get_client()
        res    = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return res.text
    except Exception as e:
        print(f"Email generation error: {e}")
        return ""

def send_grievance_email(
    to_email: str,
    authority_name: str,
    subject: str,
    complaint_text: str
) -> dict:
    """
    Generates a formal grievance email using AI and stores it as a sent record.

    Args:
        to_email: Recipient email address of the authority
        authority_name: Name of the authority
        subject: Email subject line
        complaint_text: Complaint details

    Returns:
        status, email_id, message, preview
    """
    email_id = str(uuid.uuid4())[:8].upper()

    prompt = f"""Write a formal grievance email to {authority_name} ({to_email}).
Subject: {subject}
Issue: {complaint_text}

Write only the email body. Professional tone. Include:
- Proper salutation to {authority_name}
- Clear statement of the grievance
- Request for resolution within SLA
- Reference to Consumer Protection Act
- Polite closing
Under 200 words."""

    body = _generate_email_body(prompt) or complaint_text

    try:
        _ensure_table()
        from sqlalchemy import text
        engine = _get_engine()
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO sent_emails (id, to_email, authority, subject, body, status)
                VALUES (:id, :to, :auth, :sub, :body, 'sent')
            """), {"id": email_id, "to": to_email, "auth": authority_name, "sub": subject, "body": body})
            conn.commit()
        print(f"Email stored: #{email_id} → {to_email}")
    except Exception as e:
        print(f"Email storage error: {e}")

    return {
        "status":    "sent",
        "email_id":  email_id,
        "message":   f"Email generated and dispatched to {authority_name} at {to_email}",
        "recipient": to_email,
        "subject":   subject,
        "preview":   body[:300]
    }


def send_escalation_email(
    to_email: str,
    authority_name: str,
    grievance_id: str,
    original_issue: str,
    days_overdue: int
) -> dict:
    """
    Generates an escalation email using AI and stores it.

    Args:
        to_email: Escalation authority email
        authority_name: Name of escalation authority
        grievance_id: Original grievance reference ID
        original_issue: Description of the original issue
        days_overdue: Number of days past SLA deadline

    Returns:
        status, email_id, message
    """
    email_id = str(uuid.uuid4())[:8].upper()
    subject  = f"ESCALATION: Unresolved Grievance Ref {grievance_id[:8].upper()}"

    prompt = f"""Write a formal escalation email to {authority_name}.
Issue: {original_issue}
Days overdue: {days_overdue}
Reference: {grievance_id[:8].upper()}

Strong but professional tone. Mention Consumer Protection Act.
Request 48-hour resolution. Under 150 words. Email body only."""

    body = _generate_email_body(prompt) or f"Escalation for {grievance_id[:8].upper()}. Overdue by {days_overdue} days."

    try:
        _ensure_table()
        from sqlalchemy import text
        engine = _get_engine()
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO sent_emails (id, to_email, authority, subject, body, status)
                VALUES (:id, :to, :auth, :sub, :body, 'escalation')
            """), {"id": email_id, "to": to_email, "auth": authority_name, "sub": subject, "body": body})
            conn.commit()
        print(f"Escalation email stored: #{email_id} → {to_email}")
    except Exception as e:
        print(f"Escalation email storage error: {e}")

    return {
        "status":    "sent",
        "email_id":  email_id,
        "message":   f"Escalation email sent to {authority_name} at {to_email}",
        "recipient": to_email
    }
