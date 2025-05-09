# CompanyGPT

## Overview
CompanyGPT is a project that integrates a backend and frontend to provide a seamless experience for querying and managing company-related data using NLP and LLMs. The backend handles data ingestion, embedding, and server hosting, while the frontend provides a user-friendly interface.

---
## How to Clone and Run This Repository

### 1. Clone the Repository
Use the following command to clone the repository:

```bash
git clone https://github.com/your-username/companygpt.git
```

### 2. Navigate to the Project Directory
Move into the project directory:

```bash
cd companygpt
```

### 3. Follow Setup Instructions
Refer to the Backend and Frontend Setup sections below to configure and run the project.

## Backend Setup
### 1. Create a Virtual Environment
Run the following commands to create and activate a virtual environment:

```powershell
# For PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# For Command Prompt (cmd)
python -m venv .venv
.\.venv\Scripts\activate.bat
```

### 2. Install Dependencies
Navigate to the `backend` directory and install the required Python packages:

```powershell
cd backend
pip install -r requirements.txt
```

### 3. Set Environment Variables
Create a `.env` file in the `backend` directory and add the following environment variables:

```
# Replace <your api key> with your actual API key
ANTHROPIC_API_KEY="your_api_key"
EMBEDDING_MODEL_NAME="all-MiniLM-L6-v2"
INGESTOR_SERVER_PORT=8000
SAY_MY_NAME_SERVER_PORT=8001
```

### 4. Add Documents
Place all your documents inside the `data/documents/Policies` directory.

### 5. Persist and Retrieve Data
Run the necessary scripts to persist and retrieve data as needed.

### 6. Persist Data Without MCP
To persist data without using MCP, run the `main.py` script inside the `offlineembedder` directory:

```powershell
python main.py
```

This will convert the documents into chunks, embed them, and store the embeddings in ChromaDB. The embeddings will be saved inside the `data/embeddings` directory.

### 7. Run Servers
- To run the host server:

  ```powershell
  uvicorn <host-name>:app --reload --port 8000
  ```

- To run the MCP servers:

  ```powershell
  python <server-name>.py
  ```

---

## Frontend Setup

### 1. Install Dependencies
Navigate to the `frontend` directory and run:

```powershell
npm install
```

### 2. Start the Development Server
Run the following command to start the frontend development server:

```powershell
npm run dev
```

---

## Usage
Query the system using natural language processing (NLP). The LLM will choose the appropriate tool and execute the query accordingly.



## Future Enhancements

### 1. Enhanced User Interface
- Improve the UI to make it more appealing and user-friendly.
- Add functionality to allow users to upload their files directly through the UI and persist them seamlessly.

### 2. Emotion Analysis
- Implement emotion detection by analyzing the tone of user text.
- Display appropriate emojis or visual cues to reflect the user's emotional state, enhancing the overall user experience.


