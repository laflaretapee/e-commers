FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# общие зависимости бекенда
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# КОПИРУЕМ ПАПКУ auth_service ВНУТРЬ /app/auth_service
COPY auth_service /app/auth_service

# Запускаем как пакет: auth_service.main
CMD ["uvicorn", "auth_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
