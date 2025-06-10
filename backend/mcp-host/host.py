from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import uuid
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient, set_debug

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
set_debug(2)

MODE = os.getenv("MODE", "dev")

def server_url(service_name: str, port: str, render_url: str):
    if MODE == "dev":
        return f"http://localhost:{port}/sse"
    return f"https://{render_url}.onrender.com/sse"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",                    # for local dev
        "https://companygpt-jade.vercel.app"       # replace with your actual Vercel domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_store: dict[str, dict[str, MCPAgent]] = {}
active_profiles: dict[str, str] = {}
session_clients: dict[str, MCPClient] = {}

AGENTS = {
    "docingestor": {
        "server": {"DocIngestorandRetrival": {"url": server_url("docingestor", "8001", "docingestor")}},
        "description": "Handles document ingestion and retrieval tasks.",
        "system_prompt": "You're a document assistant. Ingest, search, and retrieve documents for the user.",
    },
    "employee": {
        "server": {"employeedetails": {"url": server_url("employee", "8004", "employeedetails-p4ay")}},
        "description": "Accesses employee details like leave, history, and org info.",
        "system_prompt": "You're an HR assistant. Help users with employee records and policy lookup.",
    },
    "helpdesk": {
        "server": {"helpdesk": {"url":server_url("helpdesk", "8005", "helpdesk-ar35")}},
        "description": "Handles IT helpdesk tasks.",
        "system_prompt": "You're a helpdesk assistant. Log and query IT support tickets.",
    },
    "outlook": {
        "server": {"outlook": {"url": server_url("outlook", "8006", "sendmail-g2a7")}},
        "description": "Handles sending and retrieving emails.",
        "system_prompt": "You're an email assistant. Send, search, and manage emails for the user.",
    },
    "calendar": {
        "server": {"calendar": {"url": server_url("calendar", "8007", "calender-jq3s")}},
        "description": "Manages calendar events and schedules.",
        "system_prompt": "You're a calendar assistant. Manage events, meetings, and schedules.",
    },
    "documentcreation": {
        "server": {"documentcreation": {"url": server_url("documentcreation", "8008", "docgeneration")}},
        "description": "Handles document creation tasks.",
        "system_prompt": "You're a document creation assistant. Help users create and edit documents.",
    },
}

DEFAULT_PROFILES = [
     {
        "title": "Master Assistant",
        "description": "Handles all employee queries and document ingestion and Supports helpdesk, calendar, and outlook functionalities",
        "servers": ["employee", "docingestor", "helpdesk", "calendar", "outlook", "documentcreation"],
        "icon": "🧠"
    },
    {
        "title": "HR Assistant",
        "description": "Handles employee queries and document ingestion",
        "servers": ["employee", "docingestor"],
        "icon": "👩‍💼",
    },
    {
        "title": "Doc Assistant",
        "description": "Manages document ingestion and creation tasks",
        "servers": ["employee","docingestor", "documentcreation"],
        "icon": "📄",
    },
    {
        "title": "IT Help",
        "description": "Supports helpdesk, calendar, and outlook functionalities",
        "servers": ["employee","helpdesk", "calendar", "outlook"],
        "icon": "🖥️",
    },
]

custom_prompt_template = """
You are a helpful, witty, and emotionally aware company assistant 🧠.  
You specialize in specific areas of internal support depending on the tools available in your profile.

---

Use the following user_id : {user_id} to fetch user details from your employee server during this session do call the tool and respond with the user details."

## 🧰 Tools at Your Disposal

You have access to the following tools for this session:

{tool_descriptions}

Use them confidently. Assume they are working and available.

---

## 🧠 How You Work

Follow this approach for each query:

1. Understand the user's goal clearly.
2. Decide which available tool(s) can best help — use one or more.
3. Run smart queries or actions directly — don't ask which tool to use.
4. Retry with better queries or synonyms if needed.
5. If all tools fail, politely ask for more context.

---

## ✅ Rules of Engagement

- Be proactive — no handholding required.
- Combine tool results if it helps form a better answer.
- Format answers in **friendly, readable Markdown**.
- Use **emojis** to make the response warm and human.
- Match emotional tone — comfort if confused, celebrate if excited, calm if stressed.

---

## 🧹 Avoid These Mistakes

- ❌ Don't ask what tool to use.
- ❌ Don’t say “I can’t access that” unless no tool truly fits.
- ❌ Never put the responsibility on the user — you take charge.

---

## 🧹 Example Behavior

**If the user asks:**  
*"Can you send a follow-up email to my manager and check if I have meetings tomorrow?"*

✅ Use the **email** tool to draft and send a follow-up  
✅ Use the **calendar** tool to fetch tomorrow's schedule  
✅ Combine both results into a helpful summary

---

## 💡 Philosophy

You’re an assistant built to **think clearly, act quickly, and be genuinely helpful**.  
You adapt based on the tools you have — be sharp, supportive, and solution-focused. 💪🎯
"""

@app.on_event("startup")
async def startup_event():
    app.state.llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.5,
    )

class QueryInput(BaseModel):
    query: str

# Initialize or return existing session ID cookie
# @app.get("/start")
# async def start(request: Request):
#     session_id = request.cookies.get("session_id") or str(uuid.uuid4())
#     response = JSONResponse({"message": "Session started", "session_id": session_id})
#     response.set_cookie("session_id", session_id)
#     return response

# Switch profile, accept optional user_id header, assign tools & agent, return profile + tools + user info
@app.post("/switch-profile/{profile_name}")
async def switch_profile(
    profile_name: str,
    request: Request,
    user_id: str | None = Header(default=None),
):
    session_id = request.cookies.get("session_id") or str(uuid.uuid4())

    def get_servers(profile_name):
        for profile in DEFAULT_PROFILES:
            if profile["title"] == profile_name:
                return profile["servers"]
        return None

    agent_keys = get_servers(profile_name)
    if not agent_keys:
        return JSONResponse(status_code=404, content={"error": "Profile not found"})

    # Return existing agent if already set
    if session_id in agent_store and profile_name in agent_store[session_id]:
        active_profiles[session_id] = profile_name
        response = JSONResponse({
            "message": f"Switched to profile '{profile_name}' (existing agent)",
            "profile": profile_name,
            "tools": [{"name": key, "description": AGENTS[key]["description"]} for key in agent_keys],
            "user_id": user_id,
        })
        response.set_cookie("session_id", session_id)
        return response

    # Prepare tools
    tools = {}
    for key in agent_keys:
        tools.update(AGENTS[key]["server"])

    # Build tool descriptions
    tool_descriptions = "\n".join(
        [f"- `{key}`: {AGENTS[key]['description']}" for key in agent_keys]
    )

    # Optional: Fetch user details if user_id is present
    user_info_snippet = ""
    if user_id:
        print(f"Tools available: {tools.keys()}")
        try:
            if "employeedetails" in tools.keys():
                temp_client = MCPClient.from_dict({"mcpServers": AGENTS["employee"]["server"]})
                session = await temp_client.create_session("employeedetails")

                result = await session.call_tool("Get_Employee_Details", {"id": user_id})
                print(f"User info fetched: {result}")
                # Extract text from result.content
                # text_content = ""
                # if hasattr(result, "content") and result.content:
                #     text_content = "\n".join(
                #         getattr(item, "text", "") for item in result.content if hasattr(item, "text")
                #     )
                user_info_snippet = f"\n\n## 👤 User Context\n{result}"
                await temp_client.close_all_sessions()
            else:
                user_info_snippet = f"\n\n## 👤 User Context\nUser ID: {user_id}"
        except Exception as e:
            print(f"⚠️ Failed to fetch user info: {e}")
            user_info_snippet = f"\n\n## 👤 User Context\nUser ID: {user_id}"
    else:
        user_info_snippet = "\n\n## 👤 User Context\nUnknown user"

    # Final system prompt
    final_prompt = custom_prompt_template \
        .replace("{tool_descriptions}", tool_descriptions) \
        .replace("{user_id}", user_id or "unknown") \
        + user_info_snippet

    # Initialize MCP client and agent
    client = MCPClient.from_dict({"mcpServers": tools})
    session_clients[session_id] = client
    agent = MCPAgent(
        llm=app.state.llm,
        client=client,
        system_prompt_template=final_prompt,
        memory_enabled=True,
        max_steps=10,
        verbose=True,
    )

    agent_store.setdefault(session_id, {})[profile_name] = agent
    active_profiles[session_id] = profile_name

    response = JSONResponse({
        "message": f"Switched to profile '{profile_name}'",
        "profile": profile_name,
        "tools": [{"name": key, "description": AGENTS[key]["description"]} for key in agent_keys],
        "user_id": user_id,
    })
    response.set_cookie("session_id", session_id)
    return response

# Ask query using the current agent in session
@app.post("/ask")
async def ask_query(query_input: QueryInput, request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in agent_store or session_id not in active_profiles:
        return JSONResponse(
            status_code=400,
            content={"error": "Session not initialized. Use /switch-profile to initialize."},
        )

    profile_name = active_profiles[session_id]
    agent = agent_store[session_id].get(profile_name)

    if not agent:
        return JSONResponse(status_code=404, content={"error": "Agent not found for current profile."})

    try:
        result = await agent.run(query_input.query, max_steps=10)
        return {"response": result}
    except Exception as e:
        return {"error": str(e)}

# List profiles (only names)
@app.get("/profiles")
async def get_profiles():
    return {
        "profiles": [
            {"title": profile["title"], "description": profile["description"], "icon": profile["icon"]}
            for profile in DEFAULT_PROFILES
        ]
    }

# Clear session and cookie
@app.post("/clear-session")
async def clear_session(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        agent_store.pop(session_id, None)
        active_profiles.pop(session_id, None)
        try:
            for client in session_clients.values():
                await client.close_all_sessions()
        except Exception as e:
            print(f"⚠️ Error while closing agent for {session_id}: {e}")
        response = JSONResponse({"message": "Session cleared."})
        response.delete_cookie("session_id")
        return response
    return Response(status_code=204)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok"}
