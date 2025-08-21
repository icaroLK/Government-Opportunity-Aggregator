# Base image: official Microsoft Playwright image for Python
# - Includes Python runtime
# - Includes Playwright already configured
# - "v1.54.0-jammy" = version pinned on Ubuntu Jammy (22.04)
FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

# Set working directory inside the container
WORKDIR /app

# Copy Python dependency list into the container
COPY requirements.txt /app/requirements.txt

# Install Python dependencies from requirements.txt
# Then install Playwright Chromium browser with all required system dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    playwright install --with-deps chromium

# Copy the scraper project files into the container
COPY . /app

# Default command:
# Keep the container running (no script executed by default).
# This allows you to exec into the container or run Python scripts manually.
CMD ["tail", "-f", "/dev/null"]
