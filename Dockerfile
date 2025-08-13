# Use the official Python runtime image
FROM python:3.13.6-slim-trixie

# Create the app directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 

RUN apt-get update && apt-get install -y netcat-openbsd

# Gunicorn socket dir
RUN mkdir -p /run && chmod 777 /run

# Upgrade pip
RUN pip install --upgrade pip 

# Copy requirements and install Python dependencies
COPY require.txt .
RUN pip install --no-cache-dir -r require.txt

# Install Playwright dependencies & Chromium
RUN pip install playwright \
    && playwright install --with-deps chromium

# Copy the Django project code
COPY . .

# Make entry script executable
RUN chmod +x entry.bash
