#!/bin/bash

# Usage: ./render-services.sh start|stop

API_KEY="rnd_oRMEzBrgOEzMJ9knPWAjMIfQnDXb"
ACTION=$1

# Validate input
if [[ "$ACTION" != "resume" && "$ACTION" != "suspend" ]]; then
  echo "❌ Invalid action. Use: start or stop"
  exit 1
fi

# List of service IDs from your provided JSON
SERVICE_IDS=(
  "srv-d138hrruibrs73fu83c0"  # sendmail
  "srv-d12uis3e5dus73cqjpcg"  # docgeneration
  "srv-d12ug1bipnbc73bd0hjg"  # calender
  "srv-d12tql15pdvs73d51cp0"  # helpdesk
  "srv-d12tnjumcj7s73fovisg"  # employeedetails
  "srv-d12tln15pdvs73d4s9cg"  # docingestor
  "srv-d12tbk3e5dus73cplfg0"  # companygpt
)

for SERVICE_ID in "${SERVICE_IDS[@]}"; do
  echo "⏳ $ACTION $SERVICE_ID ..."
  curl -s -X POST "https://api.render.com/v1/services/$SERVICE_ID/$ACTION" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Accept: application/json"
  echo -e "\n✅ $SERVICE_ID $ACTION complete"
done
