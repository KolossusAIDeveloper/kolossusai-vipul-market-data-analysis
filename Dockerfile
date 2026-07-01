# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime — FastAPI serves both API and static files
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy backend code
COPY backend/ /app/backend/

# Copy React build into /app/static (served by FastAPI StaticFiles)
COPY --from=frontend-build /build/dist /app/static

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
