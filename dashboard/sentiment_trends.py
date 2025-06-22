
import streamlit as st
import pandas as pd
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    dbname="reddit",
    user="postgres",
    password="postgres"
)

@st.cache_data(ttl=60)
def load_data():
    return pd.read_sql("SELECT * FROM sentiments ORDER BY timestamp DESC LIMIT 1000", conn)

st.title("Reddit Sentiment Trends")
df = load_data()

st.line_chart(df.groupby(["timestamp", "subreddit"])["sentiment_score"].mean().unstack())
