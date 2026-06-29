# Build the API image from a small official Python base.
FROM python:3.12-slim

# Don't buffer stdout/stderr (so logs show up immediately) and don't write .pyc.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY app ./app

EXPOSE 8000

# Default command (docker-compose overrides this in development to add --reload).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
