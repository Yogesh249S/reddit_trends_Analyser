FROM python:3.10
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY enhanced_processing.py .
CMD ["python", "enhanced_processing.py"]
