# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime (Python + nginx + supervisord)
FROM python:3.11-slim

# Install nginx, supervisor, curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx supervisor curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy backend code
COPY backend/ /app/backend/

# Copy React build to nginx web root
COPY --from=frontend-build /build/dist /var/www/html

# Configure nginx
COPY nginx.conf /etc/nginx/sites-available/market
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -sf /etc/nginx/sites-available/market /etc/nginx/sites-enabled/market

# Copy supervisord config
COPY supervisord.conf /etc/supervisord.conf

# Expose port 80 (nginx)
EXPOSE 80

# Allow enough startup time for both nginx and uvicorn
HEALTHCHECK --interval=15s --timeout=10s --start-period=60s --retries=5 \
  CMD curl -sf http://localhost/ > /dev/null || exit 1

CMD ["supervisord", "-c", "/etc/supervisord.conf"]
