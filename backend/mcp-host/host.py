import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
# from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from mcp_use import MCPAgent, MCPClient
import os
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Allow your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] for all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryInput(BaseModel):
    query: str
    policyKeys: str = ''

@app.post("/ask")
async def ask_query(query_input: QueryInput):
# async def main():
    print("Received query:", query_input.query)
    query = query_input.query
    client = MCPClient(
        config={
            "mcpServers": {
                # Configuration for using SSE transport
                # "DocIngestor": {
                #     "url": "http://localhost:8001/sse"
                # },
                "saymyname": {
                    "url": "http://localhost:8003/sse"
                },
                # Cofiguration for using stdio transport
                # "Docingestor": {
                #     "type": "stdio",
                #     "command": "cmd.exe",
                #     "args": [
                #         "/C",
                #         "C:\\Sangeeth\\projects\\company-gpt\\.venv\\Scripts\\activate.bat",
                #         "&&",
                #         "python",
                #         "C:\\Sangeeth\\projects\\company-gpt\\backend\\mcp-servers\\docingestor.py",
                #     ],
                # },
                # multiserver testing
                # "saymyname": {
                #     "type": "stdio",
                #     "command": "cmd.exe",
                #     "args": [
                #         "/C",
                #         "C:\\Sangeeth\\projects\\company-gpt\\.venv\\Scripts\\activate.bat",
                #         "&&",
                #         "python",
                #         "C:\\Sangeeth\\projects\\company-gpt\\backend\\mcp-servers\\saymyname.py",
                #     ],
                # },
            }
        }
    )

    #Anthriopic Model 
    # llm = ChatAnthropic(
    #     model="Claude 3 Opus",
    #     api_key=os.getenv("ANTHROPIC_API_KEY")
    # )
    llm = ChatOllama(model="llama3.1")
    agent = MCPAgent(llm=llm, client=client, max_steps=30)
    result = await agent.run(query)
    return result

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    asyncio.run(ask_query())
