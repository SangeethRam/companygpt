import json
import os
import uuid
from typing import Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()

CALENDER_SERVER_PORT = os.getenv("CALENDER_SERVER_PORT")


# Paths
BASE_URL = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_URL, ".."))
DATA_FILE = os.path.join(BACKEND_DIR, "data", "calendar_events.json")

# Load or initialize calendar data
def load_calendar():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_calendar(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

calendar_data = load_calendar()

# Create MCP server
mcp = FastMCP("Calendar", port=CALENDER_SERVER_PORT)

@mcp.tool(name="List_Calendar_Events", description="List all calendar events.")
def list_events() -> list[dict]:
    return calendar_data

@mcp.tool(name="Add_Calendar_Event", description="Add a new calendar event.")
def add_event(title: str, start: str, end: str, recurrence: Optional[str] = None) -> str:
    event = {
        "id": str(uuid.uuid4()),
        "title": title,
        "start": start,
        "end": end
    }
    if recurrence:
        event["recurrence"] = recurrence.lower()

    calendar_data.append(event)
    save_calendar(calendar_data)
    return f"✅ Event '{title}' added."

@mcp.tool(name="Delete_Calendar_Event", description="Delete event by ID.")
def delete_event(event_id: str) -> str:
    global calendar_data
    original_len = len(calendar_data)
    calendar_data = [e for e in calendar_data if e["id"] != event_id]
    save_calendar(calendar_data)

    if len(calendar_data) == original_len:
        return f"⚠️ No event found with ID {event_id}."
    return f"🗑 Event with ID {event_id} deleted."

@mcp.tool(name="Clear_All_Events", description="Clear all calendar events.")
def clear_all_events() -> str:
    global calendar_data
    calendar_data = []
    save_calendar(calendar_data)
    return "🧹 All events cleared."

@mcp.tool(name="Get_Recurring_Events", description="List all recurring events.")
def get_recurring_events() -> list[dict]:
    return [e for e in calendar_data if "recurrence" in e]

if __name__ == "__main__":
    mcp.run(transport="sse")
