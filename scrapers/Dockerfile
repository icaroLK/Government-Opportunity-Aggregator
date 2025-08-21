FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

WORKDIR /app
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt && \
    playwright install --with-deps chromium

COPY . /app
CMD ["tail", "-f", "/dev/null"]
