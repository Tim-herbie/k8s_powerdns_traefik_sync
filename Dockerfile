FROM python:3.12.3-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file separately to leverage Docker cache
COPY pts-app/src/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir psycopg2-binary

# Copy the rest of the application code
COPY pts-app/src .

# Create a non-root user and adjust ownership
RUN groupadd -r pts && useradd -r -g pts -u 1001 pts \
    && chown -R pts:pts /app

# Switch to the non-root user
USER pts

# Run the application
CMD ["python", "main.py"]
