from google.adk.tools import FunctionTool
from .db_tools import get_department_info

db_tool = FunctionTool(func=get_department_info)