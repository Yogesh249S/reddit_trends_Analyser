# processing/enhanced_processing.py
import os
import json
import time
import logging
import traceback
from datetime import datetime
import psycopg2
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RedditAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.setup_kafka()
        self.setup_database()
    
    def setup_kafka(self):
        """Setup Kafka consumer with retry logic"""
        self.consumer = None
        for attempt in range(30):
            try:
                self.consumer = KafkaConsumer(
                    'daily_reddit_trends',
                    bootstrap_servers='kafka:9092',
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,
                    group_id='enhanced-post-processor'
                )
                logger.info("Kafka consumer connected successfully")
                break
            except NoBrokersAvailable:
                logger.warning(f"Kafka not available, attempt {attempt + 1}/30, retrying in 5 seconds...")
                time.sleep(5)
        else:
            raise Exception("Kafka broker not available after multiple attempts")
    
    def setup_database(self):
        """Setup PostgreSQL connection and create tables"""
        try:
            self.conn = psycopg2.connect(
                host="postgres",
                dbname="reddit",
                user="reddit",
                password="reddit"
            )
            self.cur = self.conn.cursor()
            self.create_analysis_tables()
            logger.info("Database connected and tables created")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise
    
    def create_analysis_tables(self):
        """Create enhanced tables for analysis"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS post_analysis (
                id SERIAL PRIMARY KEY,
                post_id TEXT UNIQUE,
                created_utc TIMESTAMP,
                subreddit TEXT,
                title TEXT,
                score INT,
                num_comments INT,
                sort_type TEXT,
                timeframe TEXT,
                author TEXT,
                upvote_ratio REAL,
                flair_text TEXT,
                
                -- Sentiment Analysis
                sentiment_score REAL,
                sentiment_label TEXT,
                
                -- Content Analysis
                title_length INT,
                word_count INT,
                has_question BOOLEAN,
                has_numbers BOOLEAN,
                caps_ratio REAL,
                
                -- Engagement Metrics
                engagement_rate REAL,
                comments_to_score_ratio REAL,
                
                -- Virality Prediction
                viral_score REAL,
                predicted_viral BOOLEAN,
                
                processed_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS subreddit_metrics (
                id SERIAL PRIMARY KEY,
                subreddit TEXT,
                date DATE,
                total_posts INT,
                avg_score REAL,
                avg_comments REAL,
                avg_sentiment REAL,
                viral_posts_count INT,
                top_keywords TEXT[],
                calculated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(subreddit, date)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS keyword_trends (
                id SERIAL PRIMARY KEY,
                keyword TEXT,
                subreddit TEXT,
                date DATE,
                frequency INT,
                avg_sentiment REAL,
                avg_score REAL,
                UNIQUE(keyword, subreddit, date)
            );
            """
        ]
        
        for table_sql in tables:
            try:
                self.cur.execute(table_sql)
                self.conn.commit()
            except Exception as e:
                logger.error(f"Error creating table: {e}")
                self.conn.rollback()
    
    def analyze_sentiment(self, text):
        """Perform sentiment analysis"""
        try:
            scores = self.analyzer.polarity_scores(text)
            compound = scores['compound']
            
            if compound >= 0.05:
                label = 'positive'
            elif compound <= -0.05:
                label = 'negative'
            else:
                label = 'neutral'
                
            return compound, label
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return 0.0, 'neutral'
    
    def analyze_content(self, title):
        """Analyze content characteristics"""
        try:
            title_length = len(title)
            word_count = len(title.split())
            has_question = '?' in title
            has_numbers = bool(re.search(r'\d', title))
            caps_count = sum(1 for c in title if c.isupper())
            caps_ratio = caps_count / len(title) if title else 0
            
            return {
                'title_length': title_length,
                'word_count': word_count,
                'has_question': has_question,
                'has_numbers': has_numbers,
                'caps_ratio': caps_ratio
            }
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return {
                'title_length': 0,
                'word_count': 0,
                'has_question': False,
                'has_numbers': False,
                'caps_ratio': 0.0
            }
    
    def calculate_engagement_metrics(self, score, num_comments):
        """Calculate engagement metrics"""
        try:
            # Engagement rate (comments per upvote)
            engagement_rate = num_comments / max(score, 1)
            
            # Comments to score ratio
            comments_to_score_ratio = num_comments / max(score, 1)
            
            return engagement_rate, comments_to_score_ratio
        except Exception as e:
            logger.error(f"Engagement calculation failed: {e}")
            return 0.0, 0.0
    
    def predict_virality(self, post_data, sentiment_score, engagement_rate):
        """Simple virality prediction model"""
        try:
            viral_score = 0.0
            
            # Score-based factors
            if post_data['score'] > 1000:
                viral_score += 0.3
            elif post_data['score'] > 500:
                viral_score += 0.2
            elif post_data['score'] > 100:
                viral_score += 0.1
            
            # Engagement factors
            if engagement_rate > 0.1:
                viral_score += 0.2
            
            # Sentiment factors
            if abs(sentiment_score) > 0.5:  # Strong sentiment
                viral_score += 0.1
            
            # Content factors
            if post_data.get('sort_type') == 'hot':
                viral_score += 0.2
            
            # Time factors (newer posts have higher potential)
            post_age_hours = (time.time() - post_data['created_utc']) / 3600
            if post_age_hours < 24:
                viral_score += 0.2
            
            predicted_viral = viral_score > 0.5
            
            return viral_score, predicted_viral
        except Exception as e:
            logger.error(f"Virality prediction failed: {e}")
            return 0.0, False
    
    def process_post(self, post_data):
        """Process a single post with comprehensive analysis"""
        try:
            logger.info(f"Processing post: {post_data.get('title', 'Unknown')[:50]}...")
            
            # Sentiment analysis
            sentiment_score, sentiment_label = self.analyze_sentiment(post_data['title'])
            
            # Content analysis
            content_metrics = self.analyze_content(post_data['title'])
            
            # Engagement metrics
            engagement_rate, comments_ratio = self.calculate_engagement_metrics(
                post_data['score'], post_data['num_comments']
            )
            
            # Virality prediction
            viral_score, predicted_viral = self.predict_virality(
                post_data, sentiment_score, engagement_rate
            )
            
            # Insert into database
            insert_sql = """
                INSERT INTO post_analysis (
                    post_id, created_utc, subreddit, title, score, num_comments,
                    sort_type, timeframe, author, upvote_ratio, flair_text,
                    sentiment_score, sentiment_label, title_length, word_count,
                    has_question, has_numbers, caps_ratio, engagement_rate,
                    comments_to_score_ratio, viral_score, predicted_viral
                ) VALUES (%s, to_timestamp(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s,
                         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (post_id) DO UPDATE SET
                    score = EXCLUDED.score,
                    num_comments = EXCLUDED.num_comments,
                    processed_at = NOW()
            """
            
            self.cur.execute(insert_sql, (
                post_data['id'],
                post_data['created_utc'],
                post_data['subreddit'],
                post_data['title'],
                post_data['score'],
                post_data['num_comments'],
                post_data['sort_type'],
                post_data['timeframe'],
                post_data['author'],
                post_data['upvote_ratio'],
                post_data['flair_text'],
                sentiment_score,
                sentiment_label,
                content_metrics['title_length'],
                content_metrics['word_count'],
                content_metrics['has_question'],
                content_metrics['has_numbers'],
                content_metrics['caps_ratio'],
                engagement_rate,
                comments_ratio,
                viral_score,
                predicted_viral
            ))
            
            self.conn.commit()
            logger.info(f"Successfully processed post: {post_data['id']}")
            
        except Exception as e:
            logger.error(f"Error processing post {post_data.get('id', 'unknown')}: {e}")
            logger.error(traceback.format_exc())
            self.conn.rollback()
    
    def run(self):
        """Main processing loop"""
        logger.info("Starting Reddit analyzer...")
        
        try:
            for message in self.consumer:
                post_data = message.value
                self.process_post(post_data)
                
        except KeyboardInterrupt:
            logger.info("Shutting down analyzer...")
        except Exception as e:
            logger.error(f"Fatal error in analyzer: {e}")
            logger.error(traceback.format_exc())
        finally:
            if self.conn:
                self.conn.close()
            if self.consumer:
                self.consumer.close()

if __name__ == "__main__":
    analyzer = RedditAnalyzer()
    analyzer.run()
