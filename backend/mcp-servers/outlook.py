import os
import smtplib
from typing import Optional, List
from email.message import EmailMessage
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import logging

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
OUTLOOK_SERVER_PORT = int(os.getenv("OUTLOOK_SERVER_PORT", "8008"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("outlook_smtp_automation.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

mcp = FastMCP("OutlookSMTPAutomation", port=OUTLOOK_SERVER_PORT)

# ---------------- Send Email via SMTP ----------------

def send_email_smtp(to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> str:
    logger.info(f"Preparing to send email to {to} with subject '{subject}'")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to
    msg.set_content(body)

    # Handle attachments
    if attachments:
        for file_path in attachments:
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()
                    file_name = os.path.basename(file_path)
                    msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)
                logger.info(f"Attached file {file_name}")
            except Exception as e:
                logger.error(f"Failed to attach file {file_path}: {e}")
                return f"Failed to attach file {file_path}: {e}"

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        logger.info(f"Email successfully sent to {to}")
        return f"Email sent to {to} with subject '{subject}'."
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return f"Failed to send email: {e}"

# ---------------- MCP Tool ----------------

@mcp.tool(name="Send_Email", description="Send an email using Outlook SMTP.")
def send_email(to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> str:
    return send_email_smtp(to, subject, body, attachments)

# ---------------- Run MCP Server ----------------

if __name__ == "__main__":
    logger.info("Starting Outlook SMTP Automation MCP server.")
    mcp.run(transport="sse")
