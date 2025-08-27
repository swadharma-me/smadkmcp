# Base image
# FROM python:3.9-slim
# FROM asia-south1-docker.pkg.dev/smartifacts-446410/smdocker/smfastapi
# FROM python:3.13

FROM asia-south1-docker.pkg.dev/smartifacts-446410/smdocker/smfastapi\

COPY requirements.txt /requirements.txt

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

WORKDIR /
# Copy everything
COPY app /app
# Set environment variables
ENV PYTHONPATH=/app
ENV ADK_AGENT_LOAD_STRATEGY=python

# Expose port
EXPOSE 8000

# Entrypoint
# CMD ["bash", "adk web app"]