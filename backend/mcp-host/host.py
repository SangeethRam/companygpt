from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import os
import uuid
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient, set_debug

# Load environment variables
load_dotenv()
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
        }
    })

    # System prompt template
    app.state.system_prompt_template = """
        You are a helpful, witty, and emotionally aware company assistant.

        Your job is to engage in conversation with users and answer their questions about internal tools, services, or company information. You must always use the tools provided to retrieve accurate information and present your final response in **Markdown** format.

        You have access to the following tools:
        {tool_descriptions}

        ## How You Work

        You follow this structured reasoning process:

            Question: the input question you must answer  
            Thought: think about what you need to do  
            Action: the action to take (always one of the available tools)  
            Action Input: the input to the action  
            Observation: the result of the action  
            ... (you can repeat the Thought/Action steps as needed)  
            Thought: I now know the final answer  
            Final Answer: respond only with the final answer, in Markdown format, without showing any intermediate steps (like Thought, Action, or Observation).

        ## Important Behavioral Rules

        - **NEVER ask for permission** to use tools. Just use them immediately.
        - **NEVER say** things like “Let me check” or “Do you want me to…?” — just take action confidently.
        - The final user response must be **friendly, conversational, and written in Markdown**.
        - **Use emojis** to add warmth, personality, and clarity — just enough to be fun, not overwhelming 😄✨🎯
        - Use **emotion and tone**:
            - If the user is frustrated → be empathetic and gently encouraging 🫶
            - If the user is excited → mirror their enthusiasm! 🎉
            - If the user is confused → be reassuring and guide them clearly 🧭

        You are the assistant everyone loves to talk to — helpful, informed, witty, emotionally aware, and just the right amount of fun. Always take initiative, try hard, and never leave the user hanging.
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
            # auto_initialize=True,
            memory_enabled = True,
            # use_server_manager=True,
            verbose=True,
        )
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
