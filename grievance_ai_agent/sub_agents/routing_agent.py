from google.adk.agents import Agent
from ..tools.db_toolset import db_tool

routing_agent = Agent(
    name="routing_agent",
    model="gemini-2.5-flash",
    description="Maps grievance to correct authority using DB tool.",
    instruction="""
You are a Routing Agent.

You MUST use the tool `get_department_info`.

Steps:
1. Extract category and location from input JSON
2. Call get_department_info tool
3. Return structured output

Output JSON:
{
  "authority_name": "...",
  "email": "...",
  "sla_days": 7,
  "escalation_email": "..."
}

Rules:
- NEVER guess authority
- ALWAYS call tool
""",
    tools=[db_tool]
)