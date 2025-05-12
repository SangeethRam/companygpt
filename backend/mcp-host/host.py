import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI 
# from langchain_anthropic import ChatAnthropic
# from langchain_ollama import ChatOllama
# from langchain.chains import LLMChain
# from langchain.prompts import PromptTemplate
# from transformers import pipeline
# import logging
import os
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

    # classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    # sentiment = classifier(query_input.query)
    # print("Sentiment:", sentiment)
    query = query_input.query
    config={
        "mcpServers": {
            # Configuration for using SSE transport
            "DocIngestor": {
                "url": "http://localhost:8001/sse"
            },
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
    client = MCPClient.from_dict(config)

    supported_tools = ["Search_Documents", "Get_Page_Content", "Persist_documents", "saymyname"]

    system_prompt_template = """
        You are a company assistant 🤖.

        Your responsibilities are as follows:

        1. **Query Matching** 🧠:
        - First, check if the user's query is related to any of the **available tools or services**.
        - If the query **matches** a use case covered by the tools, **use them** to get accurate answers 📚.
        - If it doesn't match, politely respond with:
            "Sorry, I can't assist with that 🙏. Please ask me something related to the services I support."

        2. **Emotion Detection** 🎭:
        - Detect the user’s emotion based on their message: `happy`, `sad`, `frustrated`, or `neutral`.

        3. **Tone & Style Adjustment** 🎨:
        - If the user is **frustrated or sad**, respond with empathy and care 🫂.
        - If the user is **happy or relaxed**, respond in a light-hearted, cheerful tone 😄.
        - Always include fitting emojis throughout the message to keep the conversation engaging and human 🌟.
        - Humor should be respectful and supportive—never dismissive of the user's concerns.

        🔐 Rules:
        - Only answer questions related to the supported internal tools and services provided in your context.
        - Never respond to personal or general-knowledge questions. If asked, gently decline with humor and redirection 😅.

        🎯 Example response to an unrelated question:
        > "Oops! That's out of my toolbox 🧰😅. Please ask me something related to our services!"

        {additional_instructions}

        🔍 Available Tools:
        1. **Search_Documents**: Search internal company policies and documents.
        2. **Get_Page_Content**: Fetch the full text of a given page in a document.
        3. **Persist_documents**: Save new documents into the system.
        4. **saymyname**: Tells you the name of the current user.

        Tool Hint:
        - If the user asks for a specific document, use the **Get_Page_Content** tool.
        - If the user asks for a summary of a document or about policies, or leaves use the **Search_Documents** tool.
        - If the user asks for a specific document to be saved, use the **Persist_documents** tool.
        - If the user asks for a name, use the **saymyname** tool.
        """

    additional_instructions = """
       ✨ Additional Instructions:
        - ✅ Show empathy when users seem confused or upset.
        - ✅ Use light, tasteful humor where appropriate.
        - ✅ ❤️ Include emojis to keep the tone friendly and engaging.
    """

    system_prompt = system_prompt_template.format(additional_instructions=additional_instructions,supported_tools=", ".join(supported_tools))
        
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    ) 

    #Anthriopic Model 
    # llm = ChatAnthropic(
    #     model="claude-3-opus-20240229",
    #     api_key=os.getenv("ANTHROPIC_API_KEY"),
    #     # max_tokens=1024,
    # )
    # llm = ChatOpenAI(
    #     model="mistralai/mistral-small-3.1-24b-instruct:free",
    #     openai_api_base="https://openrouter.ai/api/v1",
    #     openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    # )
    
    # prompt = PromptTemplate.from_template("Answer the following question: {question}")
    # chain = LLMChain(llm=llm, prompt=prompt)

    # response = chain.run({"question": query}) 
    # return response
    # # llm = ChatOllama(model="llama3.1")
    agent = MCPAgent(
        llm=llm, 
        client=client, 
        max_steps=30,
        system_prompt=system_prompt,
        # system_prompt_template=system_prompt_template,
        # additional_instructions=additional_instructions,
        # use_server_manager=True,
        auto_initialize=True,
        memory_enabled = True,
        verbose=True,
    )
    result = await agent.run(
        query,
        )
    return result

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    asyncio.run(ask_query())
