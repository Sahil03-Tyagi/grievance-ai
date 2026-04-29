from google.adk.tools import FunctionTool
from .db_tools import get_department_info, find_similar_cases

db_tool = FunctionTool(func=get_department_info)
similar_cases_tool   = FunctionTool(func=find_similar_cases)
