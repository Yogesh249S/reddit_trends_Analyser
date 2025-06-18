# import os
# import json
# import time
# import praw
# from kafka import KafkaProducer
# from kafka.errors import NoBrokersAvailable
# # Load Reddit API credentials from environment variables
# # REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
# # REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
# # REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
#
# # Set up Kafka producer
# producer = KafkaProducer(
#     bootstrap_servers='kafka:9092',
#     value_serializer=lambda v: json.dumps(v).encode('utf-8')
# )
#
#
# # Retry logic for Kafka producer connection
# producer = None
# for _ in range(10):
#     try:
#         producer = KafkaProducer(
#             bootstrap_servers='kafka:9092',
#             value_serializer=lambda v: json.dumps(v).encode('utf-8')
#         )
#         print("Kafka producer connected.")
#         break
#     except NoBrokersAvailable:
#         print("Kafka not available yet, retrying in 5 seconds...")
#         time.sleep(5)
# else:
#     raise Exception("Kafka broker not available after multiple attempts")
#
#
# reddit = praw.Reddit(
#     client_id="bRlIDlDGhwF8Lko_eFYc1w",
#     client_secret="P5UcE9fFALLIYPjEENiV2Sgj7PkoAA",
#     user_agent="reddit-ingestor by Agitated-Wafer6565"
# )
#
# # List of subreddits to monitor
# SUBREDDITS = ["technology", "OpenAI", "worldnews"]
#
# def stream():
#     for submission in reddit.subreddit("+".join(SUBREDDITS)).stream.submissions():
# 	print(submission.title)
#         data = {
#             "title": submission.title,
#             "created_utc": submission.created_utc,
#             "subreddit": submission.subreddit.display_name,
#             "score": submission.score,
#             "num_comments": submission.num_comments
#         }
#         print(f"Sending: {data}")
#         producer.send("reddit_posts", data)
#         time.sleep(1)
#
# if __name__ == "__main__":
#     stream()


#////////////////////////////////////////////////////////////////

# daily_ingestion.py
import os
import json
import time
import praw
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# Kafka producer setup
producer = None
for _ in range(10):
    try:
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
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


