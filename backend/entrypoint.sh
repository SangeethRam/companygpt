#!/bin/sh

echo "Starting service: $SERVICE_NAME on port $PORT"

case "$SERVICE_NAME" in
  mcp-host)
    exec uvicorn mcp-host.host:app --host 0.0.0.0 --port $PORT
    ;;

  docingestor)
    exec python mcp-servers/docingestor.py
    ;;

  employeedetails)
    exec python mcp-servers/employeedetails.py
    ;;

  helpdesk)
    exec python mcp-servers/helpdesk.py
    ;;

  outlook)
    exec python mcp-servers/outlook.py
    ;;

  calendar)
    exec python mcp-servers/calender.py
    ;;

  documentcreation)
    exec python mcp-servers/docgeneration.py
    ;;

  *)
    echo "ERROR: Unknown SERVICE_NAME: $SERVICE_NAME"
    exit 1
    ;;
esac
