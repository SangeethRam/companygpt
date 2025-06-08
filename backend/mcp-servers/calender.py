import os
import uuid
import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from supabase import create_client, Client
from postgrest.exceptions import APIError
from pathlib import Path


load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("calendar_server.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Environment
CALENDER_SERVER_PORT = os.getenv("CALENDER_SERVER_PORT")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create MCP server
mcp = FastMCP("Calendar", port=CALENDER_SERVER_PORT)

# Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@mcp.tool(name="List_Calendar_Events", description="List all calendar events.")
def list_events() -> list[dict]:
    logger.info("Listing all calendar events.")
    try:
        response = supabase.table("calendar_events").select("*").execute()
        logger.info(f"Retrieved {len(response.data)} events.")
        return response.data
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        return [{"error": str(e)}]


@mcp.tool(name="Add_Calendar_Event", description="Add a new calendar event.")
def add_event(title: str, start: str, end: str, recurrence: Optional[str] = None) -> str:
    event = {
        "id": str(uuid.uuid4()),
        "title": title,
        "start": start,
        "end": end,
        "recurrence": recurrence.lower() if recurrence else None
    }
    logger.info(f"Adding event: {event}")
    try:
        supabase.table("calendar_events").insert(event).execute()
        logger.info(f"Event '{title}' added successfully.")
        return f"✅ Event '{title}' added."
    except APIError as e:
        logger.error(f"Supabase API error while adding event '{title}': {e.message}")
        return f"⚠️ Supabase API error: {e.message}"
    except Exception as e:
        logger.error(f"Unexpected error while adding event '{title}': {e}")
        return f"⚠️ Unexpected error: {str(e)}"


@mcp.tool(name="Delete_Calendar_Event", description="Delete event by ID.")
def delete_event(event_id: str) -> str:
    logger.info(f"Deleting event with ID: {event_id}")
    try:
        response = supabase.table("calendar_events").delete().eq("id", event_id).execute()
        if response.data:
            logger.info(f"Event with ID {event_id} deleted.")
            return f"🗑 Event with ID {event_id} deleted."
        logger.warning(f"No event found with ID {event_id} to delete.")
        return f"⚠️ No event found with ID {event_id}."
    except Exception as e:
        logger.error(f"Failed to delete event {event_id}: {e}")
        return f"⚠️ Failed to delete event: {str(e)}"


@mcp.tool(name="Clear_All_Events", description="Clear all calendar events.")
def clear_all_events() -> str:
    logger.info("Clearing all calendar events.")
    try:
        supabase.table("calendar_events").delete().filter("id", "not.is", "null").execute()
        logger.info("All events cleared.")
        return "🧹 All events cleared."
    except Exception as e:
        logger.error(f"Failed to clear events: {e}")
        return f"⚠️ Failed to clear events: {str(e)}"


@mcp.tool(name="Get_Recurring_Events", description="List all recurring events.")
def get_recurring_events() -> list[dict]:
    logger.info("Listing all recurring events.")
    try:
        response = supabase.table("calendar_events").select("*").not_.is_("recurrence", "null").execute()
        logger.info(f"Retrieved {len(response.data)} recurring events.")
        return response.data
    except Exception as e:
        logger.error(f"Error listing recurring events: {e}")
        return [{"error": str(e)}]


if __name__ == "__main__":
    logger.info("Starting Calendar MCP server.")
    mcp.run(transport="sse")
