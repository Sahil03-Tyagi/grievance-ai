
from sqlalchemy import create_engine, text
from grievance_ai_agent.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def get_department_info(category: str, location: str) -> dict:
    """
    Fetch authority details from AlloyDB departments table.
    
    Args:
        category: Type of grievance e.g. electricity, water, road, police
        location: City name e.g. Ghaziabad, Delhi
        
    Returns:
        Dictionary with authority_name, email, sla_days, escalation_email
    """
    with engine.connect() as conn:
        query = text("""
            SELECT authority_name, email, sla_days, escalation_authority_email
            FROM departments
            WHERE LOWER(category) = LOWER(:category)
            AND LOWER(city) = LOWER(:location)
            LIMIT 1
        """)
        result = conn.execute(query, {
            "category": category,
            "location": location
        }).fetchone()

        if not result:
            return {
                "authority_name": "Unknown Authority",
                "email": "unknown@example.com",
                "sla_days": 7,
                "escalation_email": "unknown@example.com"
            }

        return {
            "authority_name": result[0],
            "email": result[1],
            "sla_days": result[2],
            "escalation_email": result[3]
        }

def find_similar_cases(issue_text: str, category: str, limit: int = 3) -> list:
    """
    Find similar past grievance cases using AlloyDB vector similarity search.

    Args:
        issue_text: The citizen's complaint text
        category: Grievance category to filter by
        limit: Number of similar cases to return

    Returns:
        List of similar cases with resolution and days taken
    """
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                issue_summary,
                resolution,
                days_taken,
                location,
                1 - (embedding <=> embedding('text-embedding-005', :query)::vector(768)) AS similarity
            FROM precedents
            WHERE LOWER(category) = LOWER(:category)
              AND embedding IS NOT NULL
              AND 1 - (embedding <=> embedding('text-embedding-005', :query)::vector(768)) > 0.4
            ORDER BY embedding <=> embedding('text-embedding-005', :query)::vector(768)
            LIMIT :limit
        """), {
            "query":    issue_text,
            "category": category,
            "limit":    limit
        }).fetchall()

        return [
            {
                "issue_summary": row[0],
                "resolution":    row[1],
                "days_taken":    row[2],
                "location":      row[3],
                "similarity":    round(float(row[4]) * 100)
            }
            for row in result
        ]
