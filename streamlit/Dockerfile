# Base image (use same base as mcp_servers for consistency)
FROM asia-south1-docker.pkg.dev/smartifacts-446410/smdocker/smfastapi

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code and README
COPY README.md .
COPY app/ ./app/

# Expose Streamlit default port
EXPOSE 8501

# Streamlit runs as a script; set env to avoid interactive prompts and allow headless
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    PYTHONPATH=/app

# Default command to run the Streamlit app
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
