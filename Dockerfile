FROM python:3.11-slim

WORKDIR /app

# Add this only if psycopg2 fails to install
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000
CMD ["python", "run.py"]