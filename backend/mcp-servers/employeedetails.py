from mcp.server.fastmcp import FastMCP
from typing import Optional
import json
import os
from dotenv import load_dotenv

load_dotenv()
EMPDETAILS_SERVER_PORT = os.getenv("EMPDETAILS_SERVER_PORT")

# Create the MCP server
mcp = FastMCP("EmployeeDetails", port=EMPDETAILS_SERVER_PORT)

# Load data from JSON
BASE_URL = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_URL, ".."))
EMPLOYEE_DATA_PATH = os.path.join(BACKEND_DIR, "data", "employees.json")

with open(EMPLOYEE_DATA_PATH, "r") as f:
    employees = json.load(f)

def find_employee(name: str) -> Optional[dict]:
    for emp in employees:
        if emp["name"].lower() == name.lower():
            return emp
    return None

@mcp.tool(
    name="Get_Employee_Details",
    description="Retrieve basic details (name, age, all holidays) for a given employee."
)
def get_employee_details(name: str) -> str:
    emp = find_employee(name)
    if not emp:
        return f"Employee '{name}' not found."
    
    holidays = emp["holidays"]
    holidays_str = ", ".join([f"{k}: {v}" for k, v in holidays.items()])
    return f"Name: {emp['name']}\nAge: {emp['age']}\nHolidays → {holidays_str}"

@mcp.tool(
    name="Get_Holiday_By_Type",
    description="Retrieve the number of a specific holiday type for an employee."
)
def get_holiday_by_type(name: str, holiday_type: str) -> str:
    emp = find_employee(name)
    if not emp:
        return f"Employee '{name}' not found."
    
    holidays = emp.get("holidays", {})
    value = holidays.get(holiday_type.lower())
    if value is None:
        return f"Holiday type '{holiday_type}' not found for {name}."
    
    return f"{name} has {value} days of {holiday_type} leave."

@mcp.tool(
    name="List_Employees",
    description="List all employees present in the system."
)
def list_employees() -> list[str]:
    return [emp["name"] for emp in employees]

if __name__ == "__main__":
    mcp.run(transport="sse")
