# Use an official Python runtime as a base image
FROM python:3.11-slim

# Install Node.js and npm
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy frontend code and build it
COPY frontend ./frontend
RUN cd frontend && npm install && npm run build

# Copy backend code
COPY app ./app

# Expose the port Render uses
EXPOSE 10000

# Command to run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
