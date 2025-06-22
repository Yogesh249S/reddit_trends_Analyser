# daily_ingestion.py
import os
import json
import time
import praw
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# Read Kafka broker address from environment variable (MSK support)
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Kafka producer setup
producer = None
for _ in range(10):
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Kafka producer connected.")
        break
    except NoBrokersAvailable:
        print("Kafka not available yet, retrying in 5 seconds...")
        time.sleep(5)
else:
    raise Exception("Kafka broker not available after multiple attempts")

# Reddit API setup
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

SUBREDDITS = ["askreddit", "worldnews", "todayilearned"]
SORTS = ["top", "hot", "controversial"]

# Fetch top/hot/controversial posts (daily batch)
for sort in SORTS:
    for subreddit_name in SUBREDDITS:
        subreddit = reddit.subreddit(subreddit_name)
        fetch_fn = getattr(subreddit, sort)
        print(f"Fetching {sort} posts from r/{subreddit_name}")

        for time_filter in ["day", "week", "month"]:
            for post in fetch_fn(time_filter=time_filter, limit=25):
                data = {
                    "id": post.id,
                    "title": post.title,
                    "created_utc": post.created_utc,
                    "subreddit": subreddit_name,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "sort_type": sort,
                    "timeframe": time_filter,
                    "author": str(post.author) if post.author else "deleted",
                    "upvote_ratio": post.upvote_ratio,
                    "flair_text": post.link_flair_text
                }
                print("Sending:", data)
                producer.send('daily_reddit_trends', value=data)
                time.sleep(1.5)
