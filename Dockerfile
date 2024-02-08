# Use an official Python runtime as a parent image from the slim variant to reduce image size
FROM python:3.9-slim

# Set environment variables to reduce Python's output buffering, and not to generate .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Install OS dependencies (if any) using the no-install-recommends option to keep the image clean
# Example: RUN apt-get update && apt-get install -y --no-install-recommends <package-name> && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file, to cache the pip install layer
# Since your script uses only the standard library, this step is commented out but provided for future use
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code
COPY . .

# CMD command to run your script. Replace script.py with your actual script name
CMD ["python", "./junit_tests_exporter.py"]
