FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (pkg-config + cairo for pycairo used by xhtml2pdf/svglib)
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libcairo2-dev \
    postgresql-client \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create static and media directories
RUN mkdir -p staticfiles media

# Expose port
EXPOSE 8000

# Default command
CMD ["gunicorn", "fitness_coach.wsgi:application", "--bind", "0.0.0.0:8000"]
