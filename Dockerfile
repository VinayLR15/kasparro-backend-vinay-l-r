FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Create user
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app \
    && chmod +x /app/entrypoint.sh

USER appuser

# Railway injects PORT automatically
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
