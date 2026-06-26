FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código del framework
COPY edge_framework/ ./edge_framework/
COPY examples/ ./examples/
COPY docs/ ./docs/

# Puerto FastAPI
EXPOSE 8080

# Arranque por defecto
CMD ["python", "-m", "edge_framework.cli", "start", "--config", "config.yaml"]