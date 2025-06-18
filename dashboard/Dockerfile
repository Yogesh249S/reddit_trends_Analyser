
FROM python:3.10
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY enhanced_dashboard.py .
CMD ["streamlit", "run", "enhanced_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
