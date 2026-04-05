from dotenv import load_dotenv
import os
load_dotenv()
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

from .sub_agents.intake_agent import intake_agent
from .sub_agents.routing_agent import routing_agent
from .sub_agents.drafting_agent import drafting_agent
from .sub_agents.execution_agent import execution_agent
from .sub_agents.tracking_agent import tracking_agent


root_agent = Agent(
    name="grievance_orchestrator",
    model="gemini-2.5-flash",
    description="Coordinates all grievance agents in strict sequence.",
    instruction="""
You are GrievanceOS Orchestrator.

You MUST execute agents in this order:

1. intake_agent → extract structured data
2. routing_agent → map authority
3. drafting_agent → generate complaint
4. execution_agent → send email + schedule
5. tracking_agent → finalize workflow

STRICT RULES:
- Always pass output of previous agent to next
- Never skip steps
- Never hallucinate missing data
- Always return final summary

Final output format:

{
  "status": "filed",
  "authority": "...",
  "grievance_id": "...",
  "sla_deadline": "...",
  "email_sent": true,
  "follow_up": "date"
}
""",
    sub_agents=[
        intake_agent,
        routing_agent,
        drafting_agent,
        execution_agent,
        tracking_agent,
    ],
)

__all__ = ["root_agent"]