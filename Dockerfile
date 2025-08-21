FROM python:3.11-slim

# Linux dependencies for OCR
RUN apt-get update && \
    apt-get install -y tesseract-ocr libjpeg-dev zlib1g-dev

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
