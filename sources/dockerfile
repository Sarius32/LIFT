# Use a slim Python 3.12 base image
FROM python:3.12-slim

# Set working directory
WORKDIR /workspace

# Copy requirements and install them first (for better caching)
COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the workflow files
COPY /workflow .

# Default command to run
CMD ["python", "main.py"]
