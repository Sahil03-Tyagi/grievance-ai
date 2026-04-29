import uuid
import json
from datetime import datetime, timedelta
from sqlalchemy import text
from ..tools.db_tools import engine


def log_grievance(
    category: str,
    location: str,
    issue_summary: str,
    authority_name: str,
    authority_email: str,
    sla_days: int
) -> dict:
    """
    Saves grievance and reasoning logs to AlloyDB.

    Args:
        category: Type of grievance
        location: City name
        issue_summary: Short description of issue
        authority_name: Name of authority to file with
        authority_email: Email of authority
        sla_days: Days allowed for resolution

    Returns:
        grievance_id, sla_deadline, status
    """
    grievance_id = str(uuid.uuid4())
    sla_deadline = (datetime.now() + timedelta(days=sla_days)).strftime("%Y-%m-%d")

    with engine.connect() as conn:

        # Duplicate check
        existing = conn.execute(text("""
            SELECT id FROM grievances
            WHERE category = :cat
              AND location = :loc
              AND issue_summary = :summary
              AND created_at > NOW() - INTERVAL '60 seconds'
            LIMIT 1
        """), {
            "cat":     category,
            "loc":     location,
            "summary": issue_summary
        }).fetchone()

        if existing:
            return {
                "grievance_id": str(existing[0]),
                "status":       "already_filed",
                "sla_deadline": sla_deadline,
                "message":      "Duplicate detected. Returning existing grievance."
            }

        # Save grievance with citizen details
        conn.execute(text("""
            INSERT INTO grievances
              (id, user_input, category, location, issue_summary,
               status, sla_deadline, escalation_level)
            VALUES
              (:id, :input, :cat, :loc, :summary,
               'filed', :sla, 0)
        """), {
            "id":      grievance_id,
            "input":   issue_summary,
            "cat":     category,
            "loc":     location,
            "summary": issue_summary,
            "sla":     sla_deadline
        })

        # Log all agent decisions
        logs = [
            (
                "classifier_agent",
                "classify_and_route",
                f"Identified as {category} grievance in {location}. Mapped to {authority_name} with SLA of {sla_days} days.",
                json.dumps({"issue": issue_summary, "location": location}),
                json.dumps({"authority": authority_name, "email": authority_email})
            ),
            (
                "drafting_agent",
                "draft_complaint",
                f"Formal complaint drafted for {category} issue. Legal tone applied. Addressed to {authority_name}",
                json.dumps({"category": category, "authority": authority_name}),
                json.dumps({"complaint_drafted": True})
            ),
            (
                "execution_agent",
                "send_and_schedule",
                f"Complaint dispatched to {authority_email}. Follow-up reminder scheduled for {sla_deadline}.",
                json.dumps({"email": authority_email}),
                json.dumps({"email_sent": True, "follow_up": sla_deadline})
            ),
            (
                "tracking_agent",
                "start_tracking",
                f"Grievance tracking initiated. SLA deadline {sla_deadline}. Auto-escalation triggers if unresolved.",
                json.dumps({"grievance_id": grievance_id, "sla_deadline": sla_deadline}),
                json.dumps({"status": "filed", "next_check": sla_deadline})
            ),
        ]

        for agent_name, action, reasoning, input_data, output_data in logs:
            conn.execute(text("""
                INSERT INTO workflow_logs
                  (grievance_id, agent_name, action, reasoning,
                   input_data, output_data, timestamp)
                VALUES
                  (:gid, :agent, :action, :reasoning,
                   :input_data, :output_data, NOW())
            """), {
                "gid":         grievance_id,
                "agent":       agent_name,
                "action":      action,
                "reasoning":   reasoning,
                "input_data":  input_data,
                "output_data": output_data
            })

        conn.commit()

    return {
        "grievance_id":  grievance_id,
        "status":        "filed",
        "sla_deadline":  sla_deadline,
        "next_check":    sla_deadline
    }

def get_grievance_status(keyword: str) -> dict:
    """
    Finds grievance status by keyword search in complaints.

    Args:
        keyword: Word or phrase to search in complaints

    Returns:
        Most recent matching grievance with status and reasoning trace
    """
    with engine.connect() as conn:

        result = conn.execute(text("""
            SELECT id, category, location, issue_summary,
                   status, sla_deadline, escalation_level, created_at
            FROM grievances
            WHERE LOWER(user_input) LIKE LOWER(:kw)
               OR LOWER(issue_summary) LIKE LOWER(:kw)
            ORDER BY created_at DESC
            LIMIT 1
        """), {"kw": f"%{keyword}%"}).fetchone()

        if not result:
            return {
                "found":   False,
                "message": "No grievance found matching that description."
            }

        grievance_id = str(result[0])

        logs = conn.execute(text("""
            SELECT agent_name, action, reasoning, timestamp
            FROM workflow_logs
            WHERE grievance_id = :id
            ORDER BY timestamp ASC
        """), {"id": grievance_id}).fetchall()

        return {
            "found":            True,
            "grievance_id":     grievance_id,
            "category":         result[1],
            "location":         result[2],
            "issue_summary":    result[3],
            "status":           result[4],
            "sla_deadline":     str(result[5]),
            "escalation_level": result[6],
            "filed_on":         str(result[7]),
            "reasoning_trace": [
                {
                    "agent":     r[0],
                    "action":    r[1],
                    "reasoning": r[2],
                    "timestamp": str(r[3])
                }
                for r in logs
            ]
        }
