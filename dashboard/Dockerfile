
FROM python:3.10
WORKDIR /app
COPY ../requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY sentiment_trends.py .
CMD ["streamlit", "run", "sentiment_trends.py", "--server.port=8501", "--server.address=0.0.0.0"]
