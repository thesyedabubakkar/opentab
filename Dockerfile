# OpenTab 24/7 Cloud Dockerfile (Optimized for Render.com)
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set environment
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Install system ffmpeg, fonts, and Node.js 20 LTS
RUN apt-get update && apt-get install -y curl gnupg ca-certificates ffmpeg fonts-dejavu-core fonts-freefont-ttf \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Node dependencies
COPY package.json package-lock.json* ./
RUN npm install --production

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Playwright Chromium is installed
RUN playwright install chromium

# Copy application files
COPY . .

# Permissions for startup script
RUN chmod +x start.sh

# Expose Render default port
EXPOSE 10000

# Start OpenTab service
CMD ["./start.sh"]
