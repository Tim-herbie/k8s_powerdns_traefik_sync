FROM python:3.12.3-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements and python code file into the container
COPY pts-app/src .

# Install the PostgreSQL development package, Python dependencies and other necessary dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir psycopg2-binary

# Create a non-root user, group with a specified UID/GID and change the ownership of the application directory
RUN groupadd -r pts && useradd -r -g pts -u 1001 pts \
    && chown -R pts:pts /app

# Switch to the non-root user
USER pts

# Run the application
CMD ["python", "main.py"]
