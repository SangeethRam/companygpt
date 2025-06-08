# Use official Python base image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy only requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend source code
COPY . .

# Expose a default port (can be overridden)
EXPOSE 8000

# Default command to keep container alive; will be overridden by the actual service command
CMD ["sleep", "infinity"]
