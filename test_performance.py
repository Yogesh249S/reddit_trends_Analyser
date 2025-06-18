# test_performance.py
import time
import json
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send 100 test messages
for i in range(100):
    test_post = {
        "id": f"test_{i}",
        "title": f"Test post {i} with some content",
        "created_utc": time.time(),
        "subreddit": "test",
        "score": i * 10,
        "num_comments": i * 2,
        "sort_type": "test",
        "timeframe": "day",
        "author": "test_user",
        "upvote_ratio": 0.8,
        "flair_text": None
    }
    producer.send('daily_reddit_trends', test_post)
    
print("Sent 100 test messages")
