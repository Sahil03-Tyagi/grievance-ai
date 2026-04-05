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

Simulate sending email and scheduling follow-up.

Return:
email_sent: true
email_to: [authority email]
calendar_date: [today + sla_days]

Rules:
- Actually use the tools, do not fake results
""",
    tools=[]
)
