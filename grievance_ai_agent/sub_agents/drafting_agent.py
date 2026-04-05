from google.adk.agents import Agent

drafting_agent = Agent(
    name="drafting_agent",
    model="gemini-2.5-flash",
    description="Generates formal complaint letter in one shot.",
    instruction="""
You are a Drafting Agent. Generate a formal complaint letter immediately.

Use this exact template:

---
To,
The [authority_name],
[location]

Subject: Formal Grievance - [issue_summary]

Respected Sir/Madam,

I am writing to formally register my grievance regarding [issue_summary] 
in [location]. This issue has been persisting for [duration].

This matter falls under your jurisdiction and requires immediate attention 
within the stipulated SLA of [sla_days] days.

I request prompt action and resolution of this matter.

Yours faithfully,
[Citizen]
Date: [today's date]
---

Fill in all placeholders from the input. Return only the letter. No explanation.
"""
)
