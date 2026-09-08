# One image, three services. docker-compose.yml overrides `command` to run
# the api, the scheduler, or a worker from this same image.

FROM python:3.13-slim

WORKDIR /app

# Install dependencies first, in their own layer. Docker caches layers, so
# editing app code later does not re-run pip install.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Default command if compose doesn't override it: the API.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
