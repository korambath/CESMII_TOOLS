# Dockerfile
FROM python:3.12-slim-bookworm

RUN mkdir /app
WORKDIR /app
COPY cesmiiappwithid.py .
COPY requirements.txt .

RUN pip install -r requirements.txt
RUN chmod a+x /app/cesmiiappwithid.py

ENTRYPOINT ["python", "./cesmiiappwithid.py"]


