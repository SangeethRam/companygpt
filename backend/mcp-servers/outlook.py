import os
from typing import List, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

load_dotenv()

BASE_URL = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_URL, ".."))
USER_DATA_DIR = os.path.join(BACKEND_DIR, "data", "edge-user-data")
OUTLOOK_SERVER_PORT = os.getenv("OUTLOOK_SERVER_PORT")
OUTLOOK_URL = "https://outlook.office.com"

mcp = FastMCP("OutlookAutomation", port=OUTLOOK_SERVER_PORT, dependencies=["playwright"])

# --- Helper Functions ---

# async def launch_chrome_with_profile():
#     playwright = await async_playwright().start()

#     # Use real Chrome executable, adjust path for your OS if needed
#     chrome_path = (
#         "/usr/bin/google-chrome"
#         if os.name != "nt"
#         else r"C:\Program Files\Google\Chrome\Application\chrome.exe"
#     )

#     browser = await playwright.chromium.launch_persistent_context(
#         USER_DATA_DIR,
#         headless=False,  # Show browser so user can login if needed
#         executable_path=chrome_path,
#         viewport={"width": 1280, "height": 800},
#     )
#     return playwright, browser

async def launch_edge_with_profile():
    playwright = await async_playwright().start()

    # Detect Edge executable path by OS
    if os.name == "nt":
        # Default Edge install location on Windows
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    browser = await playwright.chromium.launch_persistent_context(
        USER_DATA_DIR,
        headless=False,  # Show browser for login if needed
        executable_path=edge_path,
        viewport={"width": 1280, "height": 800},
    )
    return playwright, browser

async def outlook_send_email(page, to: str, subject: str, body: str, attachments: Optional[List[str]] = None):
    await page.goto(OUTLOOK_URL + "/mail/")
    await page.wait_for_load_state("networkidle")

    await page.click('button[aria-label="New mail"]')
    to_div = page.locator('div[aria-label="To"][contenteditable="true"]')
    await to_div.click()
    await to_div.fill('')  # Clear existing if needed (sometimes works, sometimes doesn’t)
    await to_div.type(to)
    await page.fill('input[aria-label="Subject"]', subject)

    # Fill the contenteditable message body by clicking and typing
    body_div = page.locator('div[aria-label*="Message body"]')
    await body_div.click()
    await body_div.evaluate("element => element.innerText = ''")  # Clear existing text
    await page.keyboard.type(body)

    if attachments:
        for file_path in attachments:
            await page.set_input_files('input[type="file"]', file_path)

    await page.click('button[aria-label="Send"]')

async def outlook_get_emails(page, count: int = 5) -> List[str]:
    await page.goto(OUTLOOK_URL + "/mail/")
    await page.wait_for_load_state("networkidle")
    # This selector may need updating if Outlook UI changes
    email_rows = page.locator('div[role="listbox"] div[role="option"]')
    print("Found email rows:", await email_rows.count())
    print("Email rows locator:", email_rows)
    aria_labels = await email_rows.evaluate_all('(elements) => elements.map(e => e.getAttribute("aria-label"))')

    return [f"Email #{i + 1}: {label}" for i, label in enumerate(aria_labels[:count])]

async def outlook_mark_as_read(page, email_subject: str):
    await page.goto(OUTLOOK_URL + "/mail/")
    await page.wait_for_load_state("networkidle")
    subject_locator = page.locator(f"text={email_subject}")
    outer_container = subject_locator.locator("xpath=ancestor::div[@role='option']")
    outer_container.wait_for(state="visible")

    # OPTIONAL: print the outer container's text for debugging
    text = await outer_container.text_content()
    print("Email content:", text)

    # Click the "Mark as read" button
    mark_as_read_button = outer_container.locator("button[title='Mark as read']")
    await mark_as_read_button.wait_for(state="visible")

    # Click to mark as read
    await mark_as_read_button.click()

    print("Email marked as read.")

    # Optional: Wait a bit to verify visually
    await page.wait_for_timeout(2000)

async def outlook_reply_to_email(page, email_subject: str, reply_body: str):
    await page.goto(OUTLOOK_URL + "/mail/")
    await page.wait_for_load_state("networkidle")

    # Locate and click the email by subject
    outer_container = page.locator(f"text={email_subject}")
    email_locator = outer_container.locator("xpath=ancestor::div[@role='option']")
    print("Email locator content:", await email_locator.text_content())
    print("Email locator count:", await email_locator.count())
    if await email_locator.count() == 0:
        raise ValueError(f"No email found with subject containing: {email_subject}")
    await email_locator.first.click()
    await page.wait_for_timeout(1000)

    # Click "Reply" button
    reply_button = email_locator.first.locator('button[aria-label="Reply"]')
    # Fallback: If not found inside, search globally for the more appropriate one
    if await reply_button.count() == 0:
        reply_button = page.locator('button[aria-label="Reply"]').first

    await reply_button.click()

    # Type reply in message body
    body_div = page.locator('div[aria-label*="Message body"]')
    await body_div.click()
    await body_div.evaluate("element => element.innerText = ''")  # Clear existing text
    await page.keyboard.type(reply_body)

    # Click Send
    send_button = page.locator('button[aria-label="Send"]')
    if await send_button.count() == 0:
        raise ValueError("Could not find the 'Send' button.")
    await send_button.click()

# --- MCP Tools ---

@mcp.tool(
    name="Send_Email",
    description="Send an email using Outlook."
)
async def send_email(to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> str:
    playwright, browser = await launch_edge_with_profile()
    page = await browser.new_page()
    try:
        await page.goto(OUTLOOK_URL + "/mail/")
        await page.wait_for_load_state("networkidle")

        # Check if login needed
        if "login" in page.url or "signin" in page.url:
            return "Please log in to Outlook in the opened window, then try again."

        await outlook_send_email(page, to, subject, body, attachments)
        return f"Email sent to {to} with subject '{subject}'."
    finally:
        await browser.close()
        await playwright.stop()

@mcp.tool(
    name="Get_Latest_Emails",
    description="Fetch the latest N emails from the inbox."
)
async def get_latest_emails(count: int = 5) -> List[str]:
    playwright, browser = await launch_edge_with_profile()
    page = await browser.new_page()
    try:
        await page.goto(OUTLOOK_URL + "/mail/")
        await page.wait_for_load_state("networkidle")

        if "login" in page.url or "signin" in page.url:
            return ["Please log in to Outlook in the opened Chrome window, then try again."]

        emails = await outlook_get_emails(page, count)
        return emails
    finally:
        await browser.close()
        await playwright.stop()

@mcp.tool(
    name="Mark_Email_As_Read",
    description="Mark a specific email as read."
)
async def mark_email_as_read(email_subject: str) -> str:
    playwright, browser = await launch_edge_with_profile()
    page = await browser.new_page()
    try:
        await page.goto(OUTLOOK_URL + "/mail/")
        await page.wait_for_load_state("networkidle")

        if "login" in page.url or "signin" in page.url:
            return "Please log in to Outlook in the opened Chrome window, then try again."

        await outlook_mark_as_read(page, email_subject)
        return f"Email with subject '{email_subject}' marked as read."
    finally:
        await browser.close()
        await playwright.stop()

@mcp.tool(
    name="Reply_To_Email",
    description="Reply to an existing email based on subject."
)
async def reply_to_email(email_subject: str, reply_body: str) -> str:
    playwright, browser = await launch_edge_with_profile()
    page = await browser.new_page()
    try:
        await page.goto(OUTLOOK_URL + "/mail/")
        await page.wait_for_load_state("networkidle")

        if "login" in page.url or "signin" in page.url:
            return "Please log in to Outlook in the opened Chrome window, then try again."

        await outlook_reply_to_email(page, email_subject, reply_body)
        return f"Reply sent to email with subject containing '{email_subject}'."
    finally:
        await browser.close()
        await playwright.stop()

# --- Start MCP Server ---

if __name__ == "__main__":
    mcp.run(transport="sse")
