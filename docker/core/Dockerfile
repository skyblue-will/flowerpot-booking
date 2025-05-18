FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the core module
COPY core/ /app/core/

# Make sure Python can find our module
ENV PYTHONPATH=/app 