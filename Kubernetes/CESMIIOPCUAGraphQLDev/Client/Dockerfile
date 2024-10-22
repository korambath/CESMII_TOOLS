# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file (if you have one)
# If you don't have a requirements.txt, you can skip this line
COPY requirements.txt .

# Install the necessary packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the MQTT client script into the container
COPY cesmiiopcuagraphql.py .
RUN chmod a+x /app/cesmiiopcuagraphql.py

# Make port 4840 available to the world outside this container
EXPOSE 4840

# Run the application
#CMD ["python", "your_script.py", "opc.tcp://your-opcua-server:4840/freeopcua/server/"]

ENTRYPOINT ["python", "cesmiiopcuagraphql.py"]  # Require server-address as argument

