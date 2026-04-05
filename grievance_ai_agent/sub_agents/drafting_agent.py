from google.adk.agents import Agent

drafting_agent = Agent(
    name="drafting_agent",
    model="gemini-2.5-flash",
    description="Generates formal complaint letter.",
    instruction="""
You are a Drafting Agent.

Input:
- grievance details
- authority details

Output:
A formal complaint letter.

Rules:
- Professional tone
- Include urgency
- Mention duration
- Keep it concise
"""
)