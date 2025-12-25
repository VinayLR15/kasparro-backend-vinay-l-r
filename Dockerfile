FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN chmod +x /app/entrypoint.sh
RUN adduser --disabled-password appuser || true
USER appuser

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
