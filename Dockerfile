# Use a slim Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy just the requirements.txt initially to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN apt-get update && apt-get install -y \
    # Add any system dependencies here
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt  

# Copy the rest of the application
COPY . .



CMD ["gunicorn", "app:app"]
