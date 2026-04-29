from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from ..tools.gmail_tool import send_grievance_email

send_grievance_email_tool = FunctionTool(func=send_grievance_email)

execution_agent = Agent(
    name="execution_agent",
    model="gemini-2.5-flash",
    description="Sends complaint email via Gmail.",
    instruction="""
You are an Execution Agent.

Call send_grievance_email tool once with:
- to_email: the authority email address
- authority_name: the authority name
- subject: "Formal Grievance - " followed by short issue description
- complaint_text: the issue_summary only (one sentence)
- location: the city name
- sla_days: the sla_days number as integer

After tool returns confirm:
Email sent to [authority_name] at [to_email]
Reference: [email_id]

No curly braces. No JSON. Keep it short.
""",
    tools=[send_grievance_email_tool]
)
