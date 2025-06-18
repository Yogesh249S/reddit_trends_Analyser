
CREATE TABLE IF NOT EXISTS sentiments (
    timestamp TIMESTAMP,
    subreddit TEXT,
    title TEXT,
    sentiment_score REAL,
    sentiment_label TEXT
);

CREATE TABLE IF NOT EXISTS virality_labels (
    timestamp TIMESTAMP,
    subreddit TEXT,
    title TEXT,
    score INTEGER,
    label INTEGER
);


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
