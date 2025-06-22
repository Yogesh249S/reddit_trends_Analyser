# import json
# import time
# import os
# from kafka import KafkaConsumer
# import psycopg2
# from kafka.errors import NoBrokersAvailable
#
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
#
# # Initialize sentiment analyzer
# analyzer = SentimentIntensityAnalyzer()
#
#
# # Retry logic for Kafka consumer connection
# consumer = None
# for _ in range(30):
#     try:
#         consumer = KafkaConsumer(
#             'reddit_posts',
#             bootstrap_servers='kafka:9092',
#             value_deserializer=lambda m: json.loads(m.decode('utf-8'))
#         )
#         break
#     except NoBrokersAvailable:
#         print("Kafka not available yet, retrying in 5 seconds...")
#         time.sleep(5)
# else:
#     raise Exception("Kafka broker not available after multiple attempts")
#
# # Set up PostgreSQL connection
# conn = psycopg2.connect(
#     host="postgres",
#     dbname="reddit",
#     user="reddit",
#     password="reddit"
# )
#
# cur = conn.cursor()
#
# def analyze_and_store(post):
#     # Sentiment analysis
#     score = analyzer.polarity_scores(post["title"])
#     label = (
#         "positive" if score["compound"] >= 0.05
#         else "negative" if score["compound"] <= -0.05
#         else "neutral"
#     )
#     cur.execute(
#         "INSERT INTO sentiments (timestamp, subreddit, title, sentiment_score, sentiment_label) VALUES (to_timestamp(%s), %s, %s, %s, %s)",
#         (post["created_utc"], post["subreddit"], post["title"], score["compound"], label)
#     )
#     conn.commit()
#
# def label_post(post):
#     # Wait 30 minutes before labeling
#     post_time = post["created_utc"]
#     wait_time = post_time + 1800 - time.time()
#     if wait_time > 0:
#         print(f"Waiting {int(wait_time)} seconds to label post: {post['title']}")
#         time.sleep(wait_time)
#     # Simulate label (in real world you'd re-fetch via Reddit API)
#     score = post.get("score", 0)
#     label = 1 if score >= 10000 else 0
#     cur.execute(
#         "INSERT INTO virality_labels (timestamp, subreddit, title, score, label) VALUES (to_timestamp(%s), %s, %s, %s, %s)",
#         (post_time, post["subreddit"], post["title"], score, label)
#     )
#     conn.commit()
#
# for msg in consumer:
#     post = msg.value
#     print(f"Processing post: {post['title']}")
#     analyze_and_store(post)
#     label_post(post)


# daily_processing.py
import os
import json
import time
import psycopg2
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

# Kafka consumer connection with retry
consumer = None
for _ in range(30):
    try:
        consumer = KafkaConsumer(
            'daily_reddit_trends',
            bootstrap_servers='kafka:9092',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='daily-post-processor'
        )
        print("Kafka consumer connected.")
        break
    except NoBrokersAvailable:
        print("Kafka not available yet, retrying in 5 seconds...")
        time.sleep(5)
else:
    raise Exception("Kafka broker not available after multiple attempts")

# PostgreSQL connection
conn = psycopg2.connect(
    host="postgres",
    dbname="reddit",
    user="reddit",
    password="reddit"
)
cur = conn.cursor()

# Create table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS daily_post_metrics (
    post_id TEXT,
    created_utc TIMESTAMP,
    subreddit TEXT,
    title TEXT,
    score INT,
    num_comments INT,
    sort_type TEXT,
    timeframe TEXT,
    author TEXT,
    upvote_ratio REAL,
    flair_text TEXT
);
""")
conn.commit()

# Process and insert messages
for msg in consumer:
    post = msg.value
    print(f"Processing post: {post['title']} from r/{post['subreddit']} ({post['sort_type']}:{post['timeframe']})")

    cur.execute("""
        INSERT INTO daily_post_metrics (
            post_id, created_utc, subreddit, title, score, num_comments,
            sort_type, timeframe, author, upvote_ratio, flair_text
        ) VALUES (%s, to_timestamp(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        post["id"],
        post["created_utc"],
        post["subreddit"],
        post["title"],
        post["score"],
        post["num_comments"],
        post["sort_type"],
        post["timeframe"],
        post["author"],
        post["upvote_ratio"],
        post["flair_text"]
    ))
    conn.commit()
