@echo off
REM Usage: run_all.bat [debug]

REM Check if debug mode is enabled
if /i "%1"=="debug" (
    set DEBUG_MODE=1
) else (
    set DEBUG_MODE=0
)

echo DEBUG_MODE is %DEBUG_MODE%

REM Decide whether cmd windows stay open (/k) or close (/c)
if "%DEBUG_MODE%"=="1" (
    set CMD_OPTS=/k
) else (
    set CMD_OPTS=/c
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if backend\mcp-servers folder exists
if not exist backend\mcp-servers (
    echo ERROR: Folder backend\mcp-servers does not exist!
    pause
    exit /b 1
)

REM Start backend servers
start cmd %CMD_OPTS% "python backend\mcp-servers\docingestor.py"
start cmd %CMD_OPTS% "python backend\mcp-servers\saymyname.py"
start cmd %CMD_OPTS% "python backend\mcp-servers\employeedetails.py"
start cmd %CMD_OPTS% "python backend\mcp-servers\helpdesk.py"
start cmd %CMD_OPTS% "python backend\mcp-servers\outlook.py"
start cmd %CMD_OPTS% "python backend\mcp-servers\calender.py"
start cmd %CMD_OPTS% "python backend\mcp-servers\docgeneration.py"

REM Wait for servers to start a bit
timeout /t 5 /nobreak >nul

REM Start mcp host
start cmd %CMD_OPTS% "uvicorn --app-dir backend\mcp-host host:app --reload --port 8000"

REM Start frontend without venv
start cmd %CMD_OPTS% "npm --prefix frontend run dev"

echo All servers, mcp host, and UI started.
pause
