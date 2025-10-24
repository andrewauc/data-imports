FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY meltano.yml .
COPY plugins/ ./plugins/

# Install custom plugins
RUN pip install -e ./plugins/tap-nationalgas
RUN pip install -e ./plugins/target-influxdb

# Initialize Meltano
RUN meltano install

# Create a script to run the pipeline
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set environment
ENV MELTANO_PROJECT_ROOT=/app
ENV MELTANO_DATABASE_URI=sqlite:////app/.meltano/meltano.db

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["schedule", "run"]
