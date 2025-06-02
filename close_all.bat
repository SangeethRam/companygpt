@echo off
REM Close all python and uvicorn and npm windows

echo Closing backend and frontend servers...

REM Close python processes running the specific scripts
taskkill /F /IM python.exe /T >nul 2>&1

REM Close uvicorn process
taskkill /F /IM uvicorn.exe /T >nul 2>&1

REM Close node (npm) process
taskkill /F /IM node.exe /T >nul 2>&1

echo All related processes terminated.
pause
