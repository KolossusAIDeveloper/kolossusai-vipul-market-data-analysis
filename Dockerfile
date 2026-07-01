# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: nginx + supervisord + Python/FastAPI runtime
FROM python:3.11-slim

# Install nginx, supervisor, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy backend code
WORKDIR /app
COPY backend/ /app/backend/

# Copy React build to nginx web root
COPY --from=frontend-build /build/dist /var/www/html/

# Configure nginx
COPY nginx.conf /etc/nginx/sites-available/default
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default \
    && rm -f /etc/nginx/sites-enabled/default.bak

# Configure supervisord
COPY supervisord.conf /app/supervisord.conf

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
  CMD curl -sf http://localhost:8000/health || exit 1

CMD ["/usr/bin/supervisord", "-c", "/app/supervisord.conf"]
