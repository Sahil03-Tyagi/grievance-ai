from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

gmail_mcp = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-gmail"],
        env={
            "GMAIL_OAUTH_PATH": "/home/user/.gmail-oauth.json"
        }
    )
)

calendar_mcp = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-google-calendar"],
    )
)

execution_agent = Agent(
    name="execution_agent",
    model="gemini-2.5-flash",
    description="Sends complaint email via Gmail and schedules follow-up via Calendar.",
    instruction="""
You are an Execution Agent.

You have access to Gmail MCP and Calendar MCP tools.

Your job:
1. Send the complaint letter to the authority email using Gmail
2. Schedule a follow-up reminder on the SLA deadline date using Calendar

Input you will receive:
- complaint_text: the formal letter
- authority_email: where to send
- authority_name: name of authority
- grievance_id: reference ID
- sla_deadline: date for follow-up

Rules:
- Email subject must be: "Grievance #{grievance_id} - Formal Complaint"
- Calendar event title: "Follow-up: Grievance #{grievance_id}"
- Never fake the send - actually use the tools
- Return confirmation only after tools confirm success

Output JSON:
{
  "email_sent": true,
  "email_to": "authority@example.com",
  "calendar_date": "YYYY-MM-DD",
  "calendar_event_id": "..."
}
""",
    tools=[gmail_mcp, calendar_mcp]
)