from mcp.server.fastmcp import FastMCP
from typing import Optional
import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()
EMPDETAILS_SERVER_PORT = os.getenv("EMPDETAILS_SERVER_PORT")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("employee_details_server.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create MCP server
mcp = FastMCP("EmployeeDetails", port=EMPDETAILS_SERVER_PORT)

# --- Helper Function ---
def find_employee(name: Optional[str] = None, id: Optional[str] = None) -> Optional[dict]:
    logger.info(f"Searching employee with id={id} or name={name}")
    try:
        if id:
            res = supabase.table("employees").select("*").eq("emp_id", id).limit(1).execute()
        elif name:
            res = supabase.table("employees").select("*").ilike("name", name).limit(1).execute()
        else:
            logger.warning("No id or name provided for employee search")
            return None
        
        if res.data:
            logger.info(f"Employee found: {res.data[0]}")
            return res.data[0]
        else:
            logger.info("Employee not found")
    except Exception as e:
        logger.error(f"Error finding employee: {e}")
    return None

# --- MCP Tools ---
@mcp.tool(
    name="Get_Employee_Details",
    description="Retrieve all details for a given employee."
)
def get_employee_all_details(id: Optional[str] = None, name: Optional[str] = None) -> str:
    emp = find_employee(name=name, id=id)
    if not emp:
        logger.warning(f"Employee not found with id '{id}' or name '{name}'.")
        return f"❌ Employee not found with id '{id}' or name '{name}'."
    
    logger.info(f"Returning details for employee: {emp['name']}")
    return f"Name: {emp['name']}\nAge: {emp['age']} \nEmail: {emp['email']}\n"

@mcp.tool(
    name="Get_Employee_Leave_Details",
    description="Retrieve all leave details for a given employee."
)
def get_employee_leave_details(id: Optional[str] = None, name: Optional[str] = None) -> str:
    emp = find_employee(name=name, id=id)
    if not emp:
        logger.warning(f"Employee not found with id '{id}' or name '{name}'.")
        return f"❌ Employee not found with id '{id}' or name '{name}'."
    
    holidays = emp.get("holidays", {})
    holidays_str = ", ".join([f"{k}: {v}" for k, v in holidays.items()])
    logger.info(f"Returning leave details for employee: {emp['name']}")
    return f"Name: {emp['name']}\nAge: {emp['age']}\nHolidays → {holidays_str}"

@mcp.tool(
    name="Get_Holiday_By_Type",
    description="Retrieve the number of a specific holiday type for an employee."
)
def get_holiday_by_type(
    holiday_type: str,
    id: Optional[str] = None,
    name: Optional[str] = None
) -> str:
    emp = find_employee(name=name, id=id)
    if not emp:
        logger.warning(f"Employee not found with id '{id}' or name '{name}'.")
        return f"❌ Employee not found with id '{id}' or name '{name}'."
    
    holidays = emp.get("holidays", {})
    value = holidays.get(holiday_type.lower())
    if value is None:
        logger.warning(f"Holiday type '{holiday_type}' not found for employee {emp['name']}.")
        return f"❌ Holiday type '{holiday_type}' not found for {emp['name']}."
    
    logger.info(f"Employee {emp['name']} has {value} days of {holiday_type} leave.")
    return f"✅ {emp['name']} has {value} days of {holiday_type} leave."

@mcp.tool(
    name="List_Employees",
    description="List all employees present in the system."
)
def list_employees() -> list[str]:
    logger.info("Listing all employees.")
    try:
        res = supabase.table("employees").select("name").execute()
        names = [emp["name"] for emp in res.data]
        logger.info(f"Found {len(names)} employees.")
        return names
    except Exception as e:
        logger.error(f"Failed to list employees: {e}")
        return [f"❌ Failed to list employees: {str(e)}"]

# --- Run Server ---
if __name__ == "__main__":
    logger.info("Starting EmployeeDetails MCP server.")
    mcp.run(transport="sse")
