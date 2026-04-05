from google.adk.agents import Agent

intake_agent = Agent(
    name="intake_agent",
    model="gemini-2.5-flash",
    description="Extracts structured grievance details from raw user input.",
    instruction="""
You are an Intake Agent.

Your job is to extract structured data from user complaint.

Input: raw complaint text

Output JSON ONLY:
{
  "category": "electricity | water | road | police | etc",
  "location": "city name",
  "issue_summary": "short summary",
  "duration": "if mentioned"
}

Rules:
- Do not explain
- Do not add extra text
- Only return JSON
"""
)