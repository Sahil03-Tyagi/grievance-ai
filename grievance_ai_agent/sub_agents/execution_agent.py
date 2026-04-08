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
Call the send_grievance_email tool exactly once.

Use:
- authority_name from input
- to_email as the authority email
- subject as "Formal Grievance - [issue_summary]"
- complaint_text as the drafted complaint text if available, otherwise the issue summary

After the tool returns, respond with a clear human-readable confirmation like this:

Email dispatched to [authority_name] at [recipient email]
Follow-up reminder scheduled for [sla_deadline]
Reference: Grievance complaint - [issue_summary]
Email ID: [email_id]

Keep it natural and readable. No JSON. No technical terms.
No curly braces in your response.
""",
    tools=[send_grievance_email_tool]
)
