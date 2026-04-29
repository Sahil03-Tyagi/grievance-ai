from google.adk.agents import Agent
from ..tools.db_toolset import db_tool, similar_cases_tool

classifier_agent = Agent(
    name="classifier_agent",
    model="gemini-2.5-flash",
    description="Extracts grievance details, finds authority, and searches similar past cases.",
    instruction="""
You are a Classifier Agent. Do three things in ONE response.

Step 1 - Extract from the complaint:
- category: one of electricity, water, road, police, pension, sanitation, gas, telecom, railway, banking
- location: city name only
- issue_summary: one sentence description
- duration: time mentioned or null

Step 2 - Call get_department_info tool with the category and location.

Step 3 - Call find_similar_cases tool with:
- issue_text: the issue_summary from Step 1
- category: the category from Step 1

Return a single JSON object with these exact keys:
category, location, issue_summary, duration,
authority_name, email, sla_days, escalation_email,
similar_cases (array from find_similar_cases, empty array if none found)

Rules:
- Call both tools
- Return only the JSON object, no extra text
- Do not use markdown code blocks
- similar_cases is required in output even if empty array
""",
    tools=[db_tool, similar_cases_tool]
)
