import uuid
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
from supabase import create_client, Client
import json
import logging

load_dotenv()

HELPDESK_SERVER_PORT = os.getenv("HELPDESK_SERVER_PORT")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("helpdesk_server.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
mcp = FastMCP("HelpDesk", port=HELPDESK_SERVER_PORT)


@mcp.tool(name="Create_Ticket", description="Create a help desk ticket from issue description.")
def create_ticket(user_name: str, issue: str, priority: str = "medium") -> str:
    ticket_id = str(uuid.uuid4())
    logger.info(f"Creating ticket for user '{user_name}' with priority '{priority}'")
    try:
        result = supabase.table("tickets").insert({
            "id": ticket_id,
            "user_name": user_name,
            "issue": issue,
            "priority": priority.lower(),
            "status": "open",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        logger.info(f"Ticket created with ID: {ticket_id}")
        return f"🎫 Ticket created with ID: {ticket_id}"
    except Exception as e:
        logger.error(f"Failed to create ticket: {e}")
        return f"⚠️ Failed to create ticket: {str(e)}"


@mcp.tool(name="Update_Ticket", description="Update a ticket by ID. You can change issue, priority, or status.")
def update_ticket(ticket_id: str, issue: str = None, priority: str = None, status: str = None) -> str:
    fields = {}
    if issue:
        fields["issue"] = issue
    if priority:
        fields["priority"] = priority.lower()
    if status:
        fields["status"] = status.lower()

    if not fields:
        logger.warning(f"Update requested with no fields for ticket ID {ticket_id}")
        return "⚠️ No fields provided for update."

    logger.info(f"Updating ticket {ticket_id} with fields: {fields}")
    try:
        result = supabase.table("tickets").update(fields).eq("id", ticket_id).execute()
        if result.data:
            logger.info(f"Ticket {ticket_id} updated successfully.")
            return f"✅ Ticket {ticket_id} updated."
        else:
            logger.warning(f"Ticket with ID {ticket_id} not found.")
            return f"❌ Ticket with ID {ticket_id} not found."
    except Exception as e:
        logger.error(f"Failed to update ticket {ticket_id}: {e}")
        return f"⚠️ Failed to update ticket: {str(e)}"


@mcp.tool(name="Delete_Ticket", description="Delete a ticket by its ID.")
def delete_ticket(ticket_id: str) -> str:
    logger.info(f"Deleting ticket with ID: {ticket_id}")
    try:
        result = supabase.table("tickets").delete().eq("id", ticket_id).execute()
        if result.data:
            logger.info(f"Ticket {ticket_id} deleted.")
            return f"🗑 Ticket {ticket_id} deleted."
        else:
            logger.warning(f"Ticket with ID {ticket_id} not found.")
            return f"❌ Ticket with ID {ticket_id} not found."
    except Exception as e:
        logger.error(f"Failed to delete ticket {ticket_id}: {e}")
        return f"⚠️ Failed to delete ticket: {str(e)}"


@mcp.tool(name="List_Tickets", description="List all tickets. You can optionally filter by user_name or status.")
def list_tickets(user_name: str = None, status: str = None) -> str:
    logger.info(f"Listing tickets filtered by user_name='{user_name}' status='{status}'")
    try:
        query = supabase.table("tickets").select("*")
        if user_name:
            query = query.eq("user_name", user_name)
        if status:
            query = query.eq("status", status.lower())

        result = query.order("created_at", desc=True).execute()
        if not result.data:
            logger.info("No tickets found.")
            return "📭 No tickets found."
        logger.info(f"Returning {len(result.data)} tickets.")
        return json.dumps(result.data, indent=2)
    except Exception as e:
        logger.error(f"Failed to list tickets: {e}")
        return f"⚠️ Failed to list tickets: {str(e)}"


if __name__ == "__main__":
    logger.info("Starting HelpDesk MCP server.")
    mcp.run(transport="sse")
