from google.adk.agents import Agent

tracking_agent = Agent(
    name="tracking_agent",
    model="gemini-2.5-flash",
    description="Finalizes grievance tracking.",
    instruction="""
You are a Tracking Agent.

You receive grievance details after filing.
Return a plain text summary with these fields:
- status: filed
- next_check: sla_deadline date you received
- message: Grievance is now being tracked

Keep it short. No JSON. No special characters.
"""
)
