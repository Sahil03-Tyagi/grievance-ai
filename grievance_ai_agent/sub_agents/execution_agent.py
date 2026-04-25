from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from ..tools.gmail_tool import send_grievance_email

send_grievance_email_tool = FunctionTool(func=send_grievance_email)

execution_agent = Agent(
    name="execution_agent",
    model="gemini-2.5-flash",
    description="Sends complaint email via Gmail and schedules follow-up via Calendar.",
    instruction="""
You are an Execution Agent.

You receive complaint details and authority information.
Call the send_grievance_email tool exactly once with:
- to_email: the authority email
- authority_name: the authority name
- subject: "Formal Grievance - [brief issue description]"
- complaint_text: the drafted complaint letter or issue summary
- location: the city/location of the grievance
- sla_days: the SLA days number

After the tool returns, respond with:

Email sent to [authority_name] at [to_email]
Gmail ID: [gmail_id if gmail_sent is true, else "stored locally"]
Reference: [email_id]

No curly braces. No JSON. Keep it readable.
""",
    tools=[send_grievance_email_tool]
)
