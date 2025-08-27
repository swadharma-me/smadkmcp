# Base image
# FROM python:3.9-slim
# FROM asia-south1-docker.pkg.dev/smartifacts-446410/smdocker/smfastapi
# FROM python:3.13

FROM asia-south1-docker.pkg.dev/smartifacts-446410/smdocker/smfastapi
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy additional files like README
COPY README.md .

# Copy application code
COPY app/ ./app/

# Expose the application port
EXPOSE 8000
# Set environment variables
ENV PYTHONPATH=/app
ENV ADK_AGENT_LOAD_STRATEGY=python

# Expose port
EXPOSE 8000

# Entrypoint
# CMD ["bash", "adk web app"]