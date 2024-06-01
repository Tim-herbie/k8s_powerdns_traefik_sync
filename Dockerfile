FROM python:3.12.3-slim

# Set the working directory inside the container
WORKDIR /app

# Install the PostgreSQL development package and other necessary dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
# Using --no-cache-dir to reduce the image size by not caching the package
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir psycopg2-binary

# Copy the rest of the application code into the container
COPY main.py .

# Create a non-root user and group with a specified UID/GID
RUN groupadd -r pts && useradd -r -g pts -u 1001 pts

# Change ownership of the application directory
RUN chown -R pts:pts /app

# Switch to the non-root user
USER pts

# Run the application
CMD ["python", "main.py"]
