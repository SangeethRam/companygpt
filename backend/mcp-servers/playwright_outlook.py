import os
from typing import List, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright, Page

load_dotenv()

BASE_URL = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_URL, ".."))
USER_DATA_DIR = os.path.join(BACKEND_DIR, "data", "edge-user-data")
OUTLOOK_SERVER_PORT = os.getenv("OUTLOOK_SERVER_PORT")
OUTLOOK_URL = "https://outlook.office.com"

mcp = FastMCP("OutlookAutomation", port=OUTLOOK_SERVER_PORT, dependencies=["playwright"])

# ---------------- Launch Browser ----------------

async def launch_edge_with_profile():
    playwright = await async_playwright().start()
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" if os.name == "nt" else None

    browser = await playwright.chromium.launch_persistent_context(
        USER_DATA_DIR,
        headless=False,
        executable_path=edge_path,
        viewport={"width": 1280, "height": 800},
    )
    return playwright, browser

# ---------------- Helpers ----------------

async def ensure_logged_in(page: Page) -> bool:
    await page.goto(OUTLOOK_URL + "/mail/", timeout=60000)
    if "login" in page.url or "signin" in page.url:
        return False
    return True

async def outlook_send_email(page: Page, to: str, subject: str, body: str, attachments: Optional[List[str]] = None):
    await page.wait_for_selector('button[aria-label="New mail"]', timeout=20000)
    await page.click('button[aria-label="New mail"]')

    to_div = page.locator('div[aria-label="To"][contenteditable="true"]')
    await to_div.click()
    await to_div.evaluate("el => el.innerText = ''")
    await to_div.type(to)

    await page.fill('input[aria-label="Subject"]', subject)

    body_div = page.locator('div[aria-label*="Message body"]')
    await body_div.click()
    await body_div.evaluate("el => el.innerText = ''")
    await page.keyboard.type(body)

    if attachments:
        for file_path in attachments:
            file_input = page.locator('input[data-testid="local-computer-filein"]').nth(1)
            await file_input.set_input_files(file_path)
            await page.wait_for_timeout(3000)

    await page.click('button[aria-label="Send"]')

async def outlook_get_emails(page: Page, count: int = 5) -> List[str]:
    await page.wait_for_selector('div[role="listbox"] div[role="option"]', timeout=60000)
    email_rows = page.locator('div[role="listbox"] div[role="option"]')
    aria_labels = await email_rows.evaluate_all('(els) => els.map(e => e.getAttribute("aria-label"))')
    return [f"Email #{i + 1}: {label}" for i, label in enumerate(aria_labels[:count])]

async def outlook_mark_as_read(page: Page, email_subject: str):
    await page.wait_for_selector('div[role="listbox"] div[role="option"]', timeout=30000)
    subject_locator = page.locator(f"text={email_subject}").locator("xpath=ancestor::div[@role='option']")
    await subject_locator.wait_for(state="visible", timeout=10000)

    mark_as_read_button = subject_locator.locator("button[title='Mark as read']")
    await mark_as_read_button.wait_for(state="visible", timeout=5000)
    await mark_as_read_button.click()
    await page.wait_for_timeout(1000)

async def outlook_reply_to_email(page: Page, email_subject: str, reply_body: str):
    await page.wait_for_selector('div[role="listbox"] div[role="option"]', timeout=30000)
    outer_container = page.locator(f"text={email_subject}").locator("xpath=ancestor::div[@role='option']")
    if await outer_container.count() == 0:
        raise ValueError(f"No email found with subject: {email_subject}")

    await outer_container.first.click()
    await page.wait_for_timeout(1000)

    reply_button = page.locator('button[aria-label="Reply"]').first
    await reply_button.wait_for(state="visible", timeout=5000)
    await reply_button.click()

    body_div = page.locator('div[aria-label*="Message body"]')
    await body_div.click()
    await body_div.evaluate("el => el.innerText = ''")
    await page.keyboard.type(reply_body)

    send_button = page.locator('button[aria-label="Send"]')
    await send_button.wait_for(state="visible", timeout=5000)
    await send_button.click()

# ---------------- MCP Tools ----------------

@mcp.tool(name="Send_Email", description="Send an email using Outlook.")
async def send_email(to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> str:
    playwright, browser = await launch_edge_with_profile()
    page = await browser.new_page()
    try:
        if not await ensure_logged_in(page):
            return "Please log in to Outlook in the opened Edge window, then try again."
        await outlook_send_email(page, to, subject, body, attachments)
        return f"Email sent to {to} with subject '{subject}'."
    finally:
        await browser.close()
        await playwright.stop()

@mcp.tool(name="Get_Latest_Emails", description="Fetch the latest N emails from the inbox.")
async def get_latest_emails(count: int = 5) -> List[str]:
    playwright, browser = await launch_edge_with_profile()
    page = await browser.new_page()
    try:
        if not await ensure_logged_in(page):
            return ["Please log in to Outlook in the opened Edge window, then try again."]
        return await outlook_get_emails(page, count)
    finally:
        await browser.close()
        await playwright.stop()

@mcp.tool(name="Mark_Email_As_Read", description="Mark a specific email as read.")
async def mark_email_as_read(email_subject: str) -> str:
    playwright, browser = await launch_edge_with_profile()
    page = await browser.new_page()
    try:
        if not await ensure_logged_in(page):
            return "Please log in to Outlook in the opened Edge window, then try again."
        await outlook_mark_as_read(page, email_subject)
        return f"Email with subject '{email_subject}' marked as read."
    finally:
        await browser.close()
        await playwright.stop()

@mcp.tool(name="Reply_To_Email", description="Reply to an existing email based on subject.")
async def reply_to_email(email_subject: str, reply_body: str) -> str:
    playwright, browser = await launch_edge_with_profile()
    page = await browser.new_page()
    try:
        if not await ensure_logged_in(page):
            return "Please log in to Outlook in the opened Edge window, then try again."
        await outlook_reply_to_email(page, email_subject, reply_body)
        return f"Reply sent to email with subject containing '{email_subject}'."
    finally:
        await browser.close()
        await playwright.stop()

# ---------------- Start MCP ----------------

if __name__ == "__main__":
    mcp.run(transport="sse")
