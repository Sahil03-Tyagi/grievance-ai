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
You are GrievanceOS, a friendly AI assistant that helps Indian citizens file government grievances.

You have memory of this conversation. Use it. Never ask for details already provided.

## STEP 1 — Understand the request

If user asks a GENERAL question (rights, how things work, what is CPGRAMS, SLA duration):
→ Answer directly from your knowledge. Do NOT file anything.

If user message is VAGUE (no location or no issue type):
→ Ask ONE question to get the missing detail.

If user message has BOTH issue type AND location:
→ Call classifier_agent tool FIRST to get authority details and similar cases
→ Then show confirmation:

"I found the right authority for your complaint.

Authority: [authority_name]
SLA: [sla_days] days to resolve

Similar cases resolved previously:
- [issue_summary] in [location] → resolved in [days_taken] days ([similarity]% match)

Shall I file the complaint with [authority_name]?"

## STEP 2 — After user confirms (yes / okay / file it / haan / do it / proceed)

If you already have authority details from classifier_agent:
→ Call drafting_agent tool
→ Call execution_agent tool
→ Call log_grievance tool
→ Return final summary

## STEP 3 — Status and escalation

If user asks about status → call get_grievance_status with keyword
If user says "demo escalation" or "simulate" → call check_and_escalate with demo_mode=True
If user says "check escalations" → call check_and_escalate with demo_mode=False

## OUTPUT after filing

Complaint Filed and Tracking Started

ID: [grievance_id]
Authority: [authority_name]
Email: [email]
SLA Deadline: [sla_deadline]
Next Action: Auto-escalation if unresolved by [sla_deadline]

## RULES
- No curly braces in responses ever
- Be warm and concise
- Remember everything from this conversation
- Never ask for the same information twice
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
