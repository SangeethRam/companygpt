#!/bin/sh
# entrypoint.sh - chooses service to run based on SERVICE_NAME env variable

if [ -z "$SERVICE_NAME" ]; then
  echo "SERVICE_NAME environment variable not set!"
  exit 1
fi

echo "Starting service: $SERVICE_NAME"

case "$SERVICE_NAME" in
  mcp-host)
    uvicorn mcp-host.host:app --host 0.0.0.0 --port $PORT
    ;;
  docingestor)
    python mcp-servers/docingestor.py
    ;;
  employeedetails)
    python mcp-servers/employeedetails.py
    ;;
  helpdesk)
    python mcp-servers/helpdesk.py
    ;;
  outlook)
    python mcp-servers/outlook.py
    ;;
  calendar)
    python mcp-servers/calender.py
    ;;
  documentcreation)
    python mcp-servers/docgeneration.py
    ;;
  *)
    echo "Unknown service: $SERVICE_NAME"
    exit 1
    ;;
esac
