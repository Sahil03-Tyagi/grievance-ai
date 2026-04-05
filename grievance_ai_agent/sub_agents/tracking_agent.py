from google.adk.agents import Agent

tracking_agent = Agent(
    name="tracking_agent",
    model="gemini-2.5-flash",
    description="Tracks grievance and sets escalation logic.",
    instruction="""
You are a Tracking Agent.

Input:
- grievance_id
- sla_deadline

Your job:
- Log grievance
- Prepare escalation tracking

Output:
{
  "status": "filed",
  "next_check": "timestamp"
}
"""
)