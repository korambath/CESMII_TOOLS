# Dockerfile
FROM python:3.12-slim-bookworm

RUN mkdir /app
WORKDIR /app
COPY cesmiiapp.py .
COPY requirements.txt .

RUN pip install -r requirements.txt
RUN chmod a+x /app/cesmiiapp.py

ENTRYPOINT ["python", "./cesmiiapp.py"]


