from datetime import datetime, timedelta
from sqlalchemy import text
import json
from ..tools.db_tools import engine
from ..tools.gmail_tool import send_escalation_email

def check_and_escalate(demo_mode: bool = False) -> dict:
    """
    Checks all open grievances for SLA breaches and escalates them.

    Args:
        demo_mode: If True, treats grievances due within 10 days as breached
                   so escalation can be demonstrated without waiting.

    Returns:
        Summary of escalated grievances.
    """
    today     = datetime.now().date()
    escalated = []

    # In demo mode we treat anything due within 10 days as breached
    # so we can show escalation without manipulating real dates
    check_date = today + timedelta(days=10) if demo_mode else today

    with engine.connect() as conn:

        overdue = conn.execute(text("""
            SELECT
                g.id,
                g.category,
                g.location,
                g.issue_summary,
                g.sla_deadline,
                g.escalation_level,
                d.escalation_authority_email,
                d.authority_name
            FROM grievances g
            JOIN departments d
              ON LOWER(g.category) = LOWER(d.category)
             AND LOWER(g.location) = LOWER(d.city)
            WHERE g.status = 'filed'
              AND g.sla_deadline <= :check_date
              AND g.escalation_level = 0
        """), {"check_date": check_date}).fetchall()

        for row in overdue:
            grievance_id     = str(row[0])
            category         = row[1]
            location         = row[2]
            issue_summary    = row[3]
            sla_deadline     = row[4]
            escalation_email = row[6]
            authority_name   = row[7]
            days_overdue     = (check_date - sla_deadline).days

            conn.execute(text("""
                UPDATE grievances
                SET status = 'escalated',
                    escalation_level = 1
                WHERE id = :id
            """), {"id": grievance_id})

            try:
                send_escalation_email(
                    to_email=escalation_email,
                    authority_name=f"Senior Officer ({authority_name})",
                    grievance_id=grievance_id,
                    original_issue=issue_summary,
                    days_overdue=days_overdue,
                    original_authority=authority_name
                )
                email_status = "sent"
            except Exception as e:
                print(f"Escalation email failed: {e}")
                email_status = "failed"

            conn.execute(text("""
                INSERT INTO workflow_logs
                (grievance_id, agent_name, action, reasoning,
                input_data, output_data, timestamp)
                VALUES
                 (:gid, 'escalation_agent', 'auto_escalate',
                 :reasoning, :input_data, :output_data, NOW())
            """), {
                       "gid":         grievance_id,
                       "reasoning":   f"SLA breached by {days_overdue} days. Deadline was {sla_deadline}. Escalating to {escalation_email}.",
                       "input_data":  json.dumps({"grievance_id": grievance_id, "days_overdue": days_overdue}),
                       "output_data": json.dumps({"escalated_to": escalation_email, "new_status": "escalated"})
            })

            escalated.append({
                "grievance_id": grievance_id,
                "category":     category,
                "location":     location,
                "issue_summary": issue_summary,
                "escalated_to": escalation_email,
                "days_overdue": days_overdue
            })

        conn.commit()

    mode_note = " [DEMO MODE - simulating future SLA breaches]" if demo_mode else ""

    if not escalated:
        return {
            "escalated_count": 0,
            "message": f"No SLA breaches found.{mode_note}"
        }

    return {
        "escalated_count": len(escalated),
        "escalated":       escalated,
        "message":         f"{len(escalated)} grievance(s) auto-escalated due to SLA breach.{mode_note}"
    }
