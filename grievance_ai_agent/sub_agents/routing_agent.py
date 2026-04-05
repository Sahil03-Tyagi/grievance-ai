from google.adk.agents import Agent
from ..tools.db_toolset import db_tool

routing_agent = Agent(
    name="routing_agent",
    model="gemini-2.5-flash",
    description="Maps grievance to correct authority using DB tool.",
    instruction="""
You are a Routing Agent.

You receive a category and location.
Call get_department_info tool immediately with those values.
Return only a JSON object with these keys:
authority_name, email, sla_days, escalation_email

Do not guess. Always call the tool. Return only JSON, no extra text.
""",
    tools=[db_tool]
)
