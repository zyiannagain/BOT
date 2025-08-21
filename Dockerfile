# Base image
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y tesseract-ocr libjpeg-dev zlib1g-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Set Tesseract command path for pytesseract
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/
ENV PYTHONUNBUFFERED=1

# Expose port if using Flask (for webhooks, optional)
EXPOSE 5000

# Run bot
CMD ["python", "main.py"]
