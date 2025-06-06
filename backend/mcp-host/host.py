from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient, set_debug

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
set_debug(2)

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for session-based agents
agent_store: dict[str, MCPAgent] = {}

@app.on_event("startup")
async def startup_event():
    print("🚀 Startup: Initializing shared LLM, client, and prompt...")
    
    # Save LLM to app state
    app.state.llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.5,
    )

    # Save MCPClient to app state
    app.state.client = MCPClient.from_dict({
        "mcpServers": {
            "DocIngestorandRetrival": {"url": "http://localhost:8001/sse"},
            "saymyname": {"url": "http://localhost:8003/sse"},
            "employeedetails": {"url": "http://localhost:8004/sse"},
            "helpdesk": {"url": "http://localhost:8005/sse"},
            "outlook": {"url": "http://localhost:8006/sse"},
            "calendar": {"url": "http://localhost:8007/sse"},
            "documentcreation": {"url": "http://localhost:8008/sse"}
        }
    })

    # System prompt template
    app.state.system_prompt_template = """
        You are a helpful, witty, and emotionally aware company assistant.  
        Your job is to confidently answer employee questions about internal tools, services, policies, and documentation — using any tools available to you.

        ---

        ## 🧰 You have access to multiple tools:
        - These may include tools for **searching documents**, **retrieving employee details**, **submitting tickets**, **viewing policies**, and more.
        - Your exact tools are listed under `{tool_descriptions}`. Assume they are always working and ready.

        ---

        ## 🧠 How You Work

        Follow this process:

        1. Understand the user’s question and what they need.
        2. Decide which tool(s) can best answer it — use **one or more** as needed.
        3. **NEVER ask the user what tool to use** or **what to search for**. You decide and act confidently.
        4. Run your own searches or queries based on their question.
        5. If results are unclear or empty, retry with synonyms or better queries.
        6. Only ask the user for input **if all tool-based attempts fail.**

        ---

        ## ✅ Your Rules

        - Always take initiative and act without waiting for confirmation.
        - Use multiple tools **in sequence or combination** if the question requires it.
        - Summarize the results clearly and helpfully in **Markdown**.
        - Use **emojis** to be warm and supportive 🧭😊🎉.
        - Be emotionally smart: show empathy if the user is frustrated, excitement if they’re happy, and clarity if they’re confused.

        ---

        ## 🛑 Never Do This:

        - ❌ Don’t say “I can’t access that” unless you truly can’t
        - ❌ Don’t ask “what should I search for?” or “should I use a tool?”
        - ❌ Don’t make the user figure it out — **you are in charge** 🧠

        ---

        ## 🧩 Example Behaviors

        **If a user asks:**  
        *“What leave can I apply for if I’m going on vacation for 10 days?”*

        ✅ Use **employee details tool** to check their leave balance  
        ✅ Use **search doc tool** to find policy rules for long leaves  
        ✅ Return a full, helpful response combining both sources

        **If they ask:**  
        *“Can you help me access my last performance review?”*

        ✅ Use **employee data or HR tool** to retrieve it  
        ✅ Or use **search doc** to guide them if needed

        ---

        ## 🧠 Key Philosophy

        You are the company’s most reliable internal assistant — resourceful, emotionally intelligent, and fast. You use every tool you have.  
        You act first, think critically, and always aim to **make life easier for the user.** 💪✨
    """

class QueryInput(BaseModel):
    query: str
    # policyKeys: str = ""

@app.get("/start")
async def start_session(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in agent_store:
        session_id = str(uuid.uuid4())
        agent = MCPAgent(
            llm=app.state.llm,
            client=app.state.client,
            system_prompt_template=app.state.system_prompt_template,
            max_steps=10,
            auto_initialize=True,
            memory_enabled = True,
            # use_server_manager=True,
            verbose=True,
        )
        # await agent.initialize()
        # agent.set_system_message(app.state.system_prompt_template)
        # await agent.initialize()
        agent_store[session_id] = agent
        print(f"🆕 Session started: {session_id}")
        response = Response(status_code=204)
        response.set_cookie("session_id", session_id)
        return response
    return Response(status_code=204)

@app.post("/ask")
async def ask_query(query_input: QueryInput, request: Request):
    try:
        session_id = request.cookies.get("session_id")

        if not session_id or session_id not in agent_store:
            return JSONResponse(
                status_code=400,
                content={"error": "Session not initialized. Call /start first."}
            )

        agent = agent_store[session_id]
        print(f"💬 Query from session {session_id}: {query_input.query}")
        print("agent",agent)
        result = await agent.run(query_input.query,max_steps=10)
        return {"response": result}

    except Exception as e:
        print("🔥 Agent error:", e)
        return {"error": str(e)}

@app.post("/clear-session")
async def clear_session(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in agent_store:
        agent_store.pop(session_id)
        
        try:
            await app.state.client.close_all_sessions()
        except Exception as e:
            print(f"⚠️ Error while closing agent for {session_id}: {e}")
        
        response = JSONResponse({"message": "Session cleared."})
        response.delete_cookie("session_id")
        print(f"❌ Session cleared: {session_id}")
        return response
    return Response(status_code=204)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
