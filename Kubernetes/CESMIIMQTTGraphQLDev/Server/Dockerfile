# Use the official Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the server code into the container
COPY mqtt_server.py .

# Install the required libraries
RUN pip install paho-mqtt

# Command to run the server
CMD ["python", "mqtt_server.py"]

