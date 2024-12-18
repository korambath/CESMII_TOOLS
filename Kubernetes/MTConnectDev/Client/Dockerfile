# Use the official Python image from the Docker Hub
FROM python:3.12-slim
#FROM bitnami/python:3.11

# Set the working directory
WORKDIR /app

# Copy the requirements file (if you have one)
# If you don't have a requirements.txt, you can skip this line
COPY requirements.txt .

RUN pip install --upgrade --force pip && pip install  -r requirements.txt

# Install the necessary packages
#RUN pip install --no-cache-dir -r requirements.txt

# Copy the MQTT client script into the container
COPY mtconnect_client_xmltojosn.py .
RUN chmod a+x /app/mtconnect_client_xmltojosn.py

EXPOSE 1883

# Command to run the MQTT client
ENTRYPOINT ["python", "mtconnect_client_xmltojosn.py" ]  # Require url-address and port as arguments

