FROM python:alpine

# Set working directory
WORKDIR /app

# Install system dependencies required for WeasyPrint
RUN apk add --no-cache \
    build-base \
    cairo-dev \
    pango-dev \
    gdk-pixbuf-dev \
    libffi-dev \
    shared-mime-info \
    harfbuzz-dev \
    py3-cffi \
    py3-pillow \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories for uploads
RUN mkdir -p static/uploads

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=5000

# Expose the port the app runs on
EXPOSE 5000

# Initialize the database on startup and run the application
CMD ["sh", "-c", "python init_db.py && python run.py"]