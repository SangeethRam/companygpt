# Use official Python base image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend source code
COPY . .

# Make entrypoint executable
RUN chmod +x ./entrypoint.sh

# Default environment variable (can be overridden by Render)
ENV SERVICE_NAME=default
ENV PORT=8000

# Entrypoint script will dispatch commands based on SERVICE_NAME
ENTRYPOINT ["./entrypoint.sh"]
