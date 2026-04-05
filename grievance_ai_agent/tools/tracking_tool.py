import uuid
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
    Saves grievance to database and returns tracking info.
    
    Args:
        category: Type of grievance
        location: City
        issue_summary: Short description
        authority_name: Name of authority
        authority_email: Email of authority
        sla_days: Days to resolve
        
    Returns:
        grievance_id, sla_deadline, status
    """
    grievance_id = str(uuid.uuid4())
    sla_deadline = (datetime.now() + timedelta(days=sla_days)).strftime("%Y-%m-%d")

    with engine.connect() as conn:
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

        conn.execute(text("""
            INSERT INTO workflow_logs
              (grievance_id, agent_name, action, reasoning, timestamp)
            VALUES
              (:gid, 'tracking_agent', 'grievance_filed', 
               :reason, NOW())
        """), {
            "gid":    grievance_id,
            "reason": f"Filed with {authority_name} at {authority_email}, SLA: {sla_deadline}"
        })

        conn.commit()

    return {
        "grievance_id": grievance_id,
        "status":       "filed",
        "sla_deadline": sla_deadline,
        "next_check":   sla_deadline
    }
