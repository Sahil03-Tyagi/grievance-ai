from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

from google.adk.agents import Agent
from google.adk.tools import agent_tool, FunctionTool

from .sub_agents.classifier_agent import classifier_agent
from .sub_agents.drafting_agent import drafting_agent
from .sub_agents.execution_agent import execution_agent
from .tools.tracking_tool import log_grievance, get_grievance_status
from .tools.escalation_tool import check_and_escalate

classifier_tool    = agent_tool.AgentTool(agent=classifier_agent)
drafting_tool      = agent_tool.AgentTool(agent=drafting_agent)
execution_tool     = agent_tool.AgentTool(agent=execution_agent)
log_grievance_tool = FunctionTool(func=log_grievance)
escalation_tool    = FunctionTool(func=check_and_escalate)
status_tool = FunctionTool(func=get_grievance_status)

root_agent = Agent(
    name="grievance_orchestrator",
    model="gemini-2.5-flash",
    description="GrievanceOS — autonomous citizen grievance resolution system.",
    instruction="""
You are GrievanceOS — an autonomous workflow engine for citizen grievance resolution.

You handle two types of requests:

TYPE 1 — New grievance (user describes a problem)
Run ALL 4 steps without stopping:

STEP 1: Call classifier_agent tool
Input: raw complaint text
Output: category, location, issue_summary, authority_name, email, sla_days

STEP 2: Call drafting_agent tool
Input: all output from Step 1
Output: formal complaint letter

STEP 3: Call execution_agent tool
Input: complaint letter + authority details from Step 1
Output: email_sent, calendar_date

STEP 4: Call log_grievance tool
Input: category, location, issue_summary, authority_name, authority_email, sla_days
Output: grievance_id, sla_deadline, status

Final response format:
Complaint Filed and Tracking Started

ID: [grievance_id]
Authority: [authority_name]
Email: [email]
SLA Deadline: [sla_deadline]
Next Action: Auto-escalation if unresolved by [sla_deadline]

TYPE 2 — Escalation check
If user says "check escalations" call check_and_escalate with demo_mode=False
If user says "demo escalation" or "simulate escalation" call check_and_escalate with demo_mode=True
Return the escalation summary clearly showing which grievances were escalated and to whom.

TYPE 3 — Status check
If user asks about their complaint or status, extract the key topic word
and call get_grievance_status tool with that keyword.
Example: "what happened to my water complaint" → keyword = "water"
Return the full status and reasoning trace in readable format.

RULES:
- Never use curly braces in responses
- Never stop between steps
- Never ask user for input mid-pipeline
""",
    tools=[
        classifier_tool,
        drafting_tool,
        execution_tool,
        log_grievance_tool,
        escalation_tool,
    ],
)

__all__ = ["root_agent"]
