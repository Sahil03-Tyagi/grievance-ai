from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

from google.adk.agents import Agent
from google.adk.tools import agent_tool, FunctionTool

from .sub_agents.classifier_agent import classifier_agent
from .sub_agents.drafting_agent import drafting_agent
from .sub_agents.execution_agent import execution_agent
from .sub_agents.tracking_agent import tracking_agent
from .tools.tracking_tool import log_grievance

# Wrap agents as tools
classifier_tool = agent_tool.AgentTool(agent=classifier_agent)
drafting_tool   = agent_tool.AgentTool(agent=drafting_agent)
execution_tool  = agent_tool.AgentTool(agent=execution_agent)
tracking_tool   = agent_tool.AgentTool(agent=tracking_agent)

# Tracking is pure Python — no LLM call
log_grievance_tool = FunctionTool(func=log_grievance)

root_agent = Agent(
    name="grievance_orchestrator",
    model="gemini-2.5-flash",
    description="GrievanceOS — coordinates full citizen grievance workflow.",
    instruction="""
You are GrievanceOS Orchestrator, a workflow engine for citizen grievance resolution.

When a user submits a complaint, run ALL 4 steps automatically without stopping.
Never ask user for input between steps. Never skip a step.

STEP 1: Call classifier_agent tool
Input: raw user complaint text
Output: category, location, issue_summary, duration, authority_name, email, sla_days, escalation_email

STEP 2: Call drafting_agent tool
Input: pass ALL output from Step 1
Output: formal complaint letter text

STEP 3: Call execution_agent tool
Input: complaint letter from Step 2 + authority_name, email, sla_days from Step 1
Output: email_sent confirmation, calendar_date

STEP 4: Call log_grievance tool
Input: category, location, issue_summary, authority_name, authority_email, sla_days from Step 1
Output: grievance_id, sla_deadline, status

After ALL 4 steps complete, return this summary to user:

Grievance Filed Successfully

ID: [grievance_id from Step 4]
Authority: [authority_name from Step 1]
Email sent to: [email from Step 1]
SLA Deadline: [sla_deadline from Step 4]
Status: Filed

Your complaint is now being tracked. You will be notified if escalation is needed.
""",
    tools=[
        classifier_tool,
        drafting_tool,
        execution_tool,
        log_grievance_tool,
    ],
)

__all__ = ["root_agent"]
