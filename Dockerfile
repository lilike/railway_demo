# Dockerfile for Railway deployment
FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libglib2.0-0 \
    libnspr4 \
    libnss3 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxcb1 \
    libxkbcommon0 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pyproject.toml and install dependencies using uv
COPY pyproject.toml uv.lock ./
RUN pip install uv && \
    uv sync --frozen --no-dev

# Install Playwright browsers and dependencies
RUN . .venv/bin/activate && playwright install-deps chromium
RUN . .venv/bin/activate && playwright install chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 8081

# Start command
CMD [".venv/bin/python", "main_backend.py"]
