# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file (if you have one)
# If you don't have a requirements.txt, you can skip this line
COPY requirements.txt .

# Install the necessary packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the MQTT client script into the container
COPY cesmiimqttgraphql.py .
RUN chmod a+x /app/cesmiimqttgraphql.py 

EXPOSE 1883

# Command to run the MQTT client
ENTRYPOINT ["python", "cesmiimqttgraphql.py" ]  # Require broker-address as argument
#CMD ["python", "cesmiimqttgraphql.py"]  # Replace with default broker address if needed

