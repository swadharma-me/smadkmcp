# Base image
# FROM python:3.9-slim
# FROM asia-south1-docker.pkg.dev/smartifacts-446410/smdocker/smfastapi
# FROM python:3.11

FROM asia-south1-docker.pkg.dev/smartifacts-446410/smdocker/smfastapi
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy additional files like README
COPY README.md .

# Copy application code
COPY app/ ./app/
# Default command to run the application
# CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-b", "0.0.0.0:8000"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]