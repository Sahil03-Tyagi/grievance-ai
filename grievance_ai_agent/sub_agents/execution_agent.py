from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

gmail_mcp = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-gmail"],
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

You receive complaint details and authority information.
Simulate sending the complaint and scheduling follow-up.

Return a clear human-readable confirmation like this:

Email dispatched to [authority_name] at [authority_email]
Follow-up reminder scheduled for [sla_deadline]
Reference: Grievance complaint - [issue_summary]

Keep it natural and readable. No JSON. No technical terms.
No curly braces in your response.
""",
    tools=[]
)
