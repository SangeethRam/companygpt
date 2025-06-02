import uuid
import json
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()
HELPDESK_SERVER_PORT = os.getenv("HELPDESK_SERVER_PORT")

mcp = FastMCP("HelpDesk", port=HELPDESK_SERVER_PORT)
BASE_URL = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_URL, ".."))
TICKET_DB = os.path.join(BACKEND_DIR, "data", "tickets.json")


def load_tickets():
    if not os.path.exists(TICKET_DB):
        return []
    with open(TICKET_DB, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_tickets(tickets):
    with open(TICKET_DB, "w") as f:
        json.dump(tickets, f, indent=2)


@mcp.tool(name="Create_Ticket", description="Create a help desk ticket from issue description.")
def create_ticket(user: str, issue: str, priority: str = "medium") -> str:
    tickets = load_tickets()
    ticket_id = str(uuid.uuid4())[:8]
    ticket = {
        "id": ticket_id,
        "user": user,
        "issue": issue,
        "priority": priority.lower(),
        "status": "open",
        "created_at": datetime.utcnow().isoformat()
    }
    tickets.append(ticket)
    save_tickets(tickets)
    return f"Ticket created with ID: {ticket_id}"


@mcp.tool(name="Update_Ticket", description="Update a ticket by ID. You can change issue, priority, or status.")
def update_ticket(ticket_id: str, issue: str = None, priority: str = None, status: str = None) -> str:
    tickets = load_tickets()
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            if issue:
                ticket["issue"] = issue
            if priority:
                ticket["priority"] = priority.lower()
            if status:
                ticket["status"] = status.lower()
            save_tickets(tickets)
            return f"Ticket {ticket_id} updated successfully."
    return f"Ticket with ID {ticket_id} not found."


@mcp.tool(name="Delete_Ticket", description="Delete a ticket by its ID.")
def delete_ticket(ticket_id: str) -> str:
    tickets = load_tickets()
    updated_tickets = [t for t in tickets if t["id"] != ticket_id]
    if len(updated_tickets) == len(tickets):
        return f"Ticket with ID {ticket_id} not found."
    save_tickets(updated_tickets)
    return f"Ticket {ticket_id} deleted successfully."


@mcp.tool(name="List_Tickets", description="List all tickets. You can optionally filter by user or status.")
def list_tickets(user: str = None, status: str = None) -> str:
    tickets = load_tickets()
    if user:
        tickets = [t for t in tickets if t["user"] == user]
    if status:
        tickets = [t for t in tickets if t["status"].lower() == status.lower()]
    if not tickets:
        return "No tickets found."
    return json.dumps(tickets, indent=2)


# Start the MCP server
if __name__ == "__main__":
    mcp.run(transport="sse")
