FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a .env file from environment variables at runtime
RUN touch .env

# Expose the port
EXPOSE 8000

# Start the application
CMD ["sh", "-c", "echo OPENAI_API_KEY=$OPENAI_API_KEY >> .env && uvicorn app.main:app --host 0.0.0.0 --port 8000"]