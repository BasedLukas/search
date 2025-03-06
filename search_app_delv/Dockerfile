FROM python:3.8-slim

WORKDIR /app

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first to leverage Docker cache
COPY pyproject.toml .

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir hatch && \
    pip install --no-cache-dir .

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "--log-level=info", "--capture-output", "application:app"]
