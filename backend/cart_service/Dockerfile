FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY cart_service /app/cart_service

CMD ["uvicorn", "cart_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
