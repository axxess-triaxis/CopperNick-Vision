FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

# Cloud Run injects $PORT; uvicorn must bind to it, not a hardcoded port.
ENV PORT=8080
CMD ["sh", "-c", "uvicorn coppernick.web:app --host 0.0.0.0 --port ${PORT}"]
