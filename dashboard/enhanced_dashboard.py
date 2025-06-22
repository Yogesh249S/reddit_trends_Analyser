# dashboard/enhanced_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psycopg2
from datetime import datetime, timedelta
import numpy as np

# Configure page
st.set_page_config(
    page_title="Reddit Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# Database connection
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="postgres",
        dbname="reddit",
        user="reddit",
        password="reddit"
    )

# Data loading functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_analysis_data():
    conn = get_connection()
    query = """
    SELECT
        post_id, created_utc, subreddit, title, score, num_comments,
        sentiment_score, sentiment_label, title_length, word_count,
        has_question, has_numbers, caps_ratio, engagement_rate,
        viral_score, predicted_viral, processed_at
    FROM post_analysis
    WHERE created_utc >= NOW() - INTERVAL '7 days'
    ORDER BY created_utc DESC
    """
    return pd.read_sql(query, conn)

@st.cache_data(ttl=300)
def load_subreddit_metrics():
    conn = get_connection()
    query = """
    SELECT
        subreddit,
        COUNT(*) as total_posts,
        AVG(score) as avg_score,
        AVG(num_comments) as avg_comments,
        AVG(sentiment_score) as avg_sentiment,
        AVG(viral_score) as avg_viral_score,
        COUNT(CASE WHEN predicted_viral THEN 1 END) as viral_posts,
        AVG(engagement_rate) as avg_engagement
    FROM post_analysis
    WHERE created_utc >= NOW() - INTERVAL '24 hours'
    GROUP BY subreddit
    ORDER BY total_posts DESC
    """
    return pd.read_sql(query, conn)

@st.cache_data(ttl=300)
def load_trending_analysis():
    conn = get_connection()
    query = """
    SELECT
        DATE_TRUNC('hour', created_utc) as hour,
        subreddit,
        AVG(sentiment_score) as avg_sentiment,
        AVG(viral_score) as avg_viral_score,
        COUNT(*) as post_count
    FROM post_analysis
    WHERE created_utc >= NOW() - INTERVAL '48 hours'
    GROUP BY DATE_TRUNC('hour', created_utc), subreddit
    ORDER BY hour DESC
    """
    return pd.read_sql(query, conn)

# Main dashboard
def main():
    st.title("🔍 Reddit Analysis Dashboard")
    st.markdown("Real-time insights from Reddit data analysis")

    # Sidebar filters
    st.sidebar.header("📊 Filters")

    try:
        # Load data
        df = load_analysis_data()
        subreddit_metrics = load_subreddit_metrics()
        trending_data = load_trending_analysis()

        if df.empty:
            st.warning("No data available. Make sure your data pipeline is running.")
            return

        # Subreddit filter
        subreddits = ['All'] + sorted(df['subreddit'].unique().tolist())
        selected_subreddit = st.sidebar.selectbox("Select Subreddit", subreddits)

        if selected_subreddit != 'All':
            df = df[df['subreddit'] == selected_subreddit]

        # Time range filter
        time_range = st.sidebar.selectbox(
            "Time Range",
            ["Last 24 hours", "Last 3 days", "Last 7 days"]
        )

        hours_map = {"Last 24 hours": 24, "Last 3 days": 72, "Last 7 days": 168}
        cutoff_time = datetime.now() - timedelta(hours=hours_map[time_range])
        df = df[pd.to_datetime(df['created_utc']) >= cutoff_time]

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📝 Total Posts", len(df))

        with col2:
            avg_sentiment = df['sentiment_score'].mean()
            st.metric("😊 Avg Sentiment", f"{avg_sentiment:.3f}")

        with col3:
            viral_posts = df['predicted_viral'].sum()
            st.metric("🔥 Viral Posts", viral_posts)

        with col4:
            avg_engagement = df['engagement_rate'].mean()
            st.metric("💬 Avg Engagement", f"{avg_engagement:.3f}")

        # Charts row 1
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Sentiment Distribution")
            sentiment_counts = df['sentiment_label'].value_counts()
            fig_sentiment = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                color_discrete_map={
                    'positive': '#00CC96',
                    'negative': '#EF553B',
                    'neutral': '#636EFA'
                }
            )
            st.plotly_chart(fig_sentiment, use_container_width=True)

        with col2:
            st.subheader("🔥 Virality Prediction")
            viral_counts = df['predicted_viral'].value_counts()
            fig_viral = px.pie(
                values=viral_counts.values,
                names=['Not Viral', 'Predicted Viral'],
                color_discrete_map={False: '#FFA15A', True: '#FF6692'}
            )
            st.plotly_chart(fig_viral, use_container_width=True)

        # Charts row 2
        st.subheader("📊 Subreddit Performance")
        if not subreddit_metrics.empty:
            fig_subreddit = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Average Score', 'Average Sentiment', 'Viral Posts', 'Engagement Rate'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )

            # Average Score
            fig_subreddit.add_trace(
                go.Bar(x=subreddit_metrics['subreddit'], y=subreddit_metrics['avg_score'], name='Avg Score'),
                row=1, col=1
            )

            # Average Sentiment
            fig_subreddit.add_trace(
                go.Bar(x=subreddit_metrics['subreddit'], y=subreddit_metrics['avg_sentiment'], name='Avg Sentiment'),
                row=1, col=2
            )

            # Viral Posts
            fig_subreddit.add_trace(
                go.Bar(x=subreddit_metrics['subreddit'], y=subreddit_metrics['viral_posts'], name='Viral Posts'),
                row=2, col=1
            )

            # Engagement Rate
            fig_subreddit.add_trace(
                go.Bar(x=subreddit_metrics['subreddit'], y=subreddit_metrics['avg_engagement'], name='Engagement'),
                row=2, col=2
            )

            fig_subreddit.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig_subreddit, use_container_width=True)

        # Trending analysis
        st.subheader("📈 Trending Analysis")
        if not trending_data.empty:
            fig_trending = px.line(
                trending_data,
                x='hour',
                y='avg_sentiment',
                color='subreddit',
                title='Sentiment Trends Over Time'
            )
            st.plotly_chart(fig_trending, use_container_width=True)

        # Content analysis
        st.subheader("📝 Content Analysis")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Word Count Distribution")
            fig_words = px.histogram(df, x='word_count', nbins=20)
            st.plotly_chart(fig_words, use_container_width=True)

        with col2:
            st.subheader("Question Posts Analysis")
            question_analysis = df.groupby('has_question').agg({
                'sentiment_score': 'mean',
                'score': 'mean',
                'engagement_rate': 'mean'
            }).reset_index()
            question_analysis['has_question'] = question_analysis['has_question'].map({True: 'Questions', False: 'Statements'})

            fig_questions = px.bar(
                question_analysis,
                x='has_question',
                y='sentiment_score',
                title='Sentiment: Questions vs Statements'
            )
            st.plotly_chart(fig_questions, use_container_width=True)

        # Top performing posts
        st.subheader("🏆 Top Performing Posts")
        top_posts = df.nlargest(10, 'viral_score')[['title', 'subreddit', 'score', 'sentiment_score', 'viral_score', 'predicted_viral']]
        st.dataframe(top_posts, use_container_width=True)

        # Real-time data table
        st.subheader("🔴 Real-time Data")
        recent_posts = df.head(20)[['created_utc', 'subreddit', 'title', 'score', 'sentiment_label', 'predicted_viral']]
        st.dataframe(recent_posts, use_container_width=True)

        # Advanced analytics
        with st.expander("🔬 Advanced Analytics"):
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Correlation Analysis")
                correlation_data = df[['score', 'num_comments', 'sentiment_score', 'viral_score', 'engagement_rate']].corr()
                fig_corr = px.imshow(correlation_data, text_auto=True, aspect="auto")
                st.plotly_chart(fig_corr, use_container_width=True)

            with col2:
                st.subheader("Content Features Impact")
                feature_impact = df.groupby(['has_question', 'has_numbers']).agg({
                    'viral_score': 'mean',
                    'sentiment_score': 'mean'
                }).reset_index()

                feature_impact['content_type'] = feature_impact.apply(
                    lambda x: f"Q:{x['has_question']}, N:{x['has_numbers']}", axis=1
                )

                fig_features = px.scatter(
                    feature_impact,
                    x='sentiment_score',
                    y='viral_score',
                    text='content_type',
                    title='Content Features vs Performance'
                )
                st.plotly_chart(fig_features, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        st.info("Make sure your database is running and contains data.")

        # Debug info
        with st.expander("Debug Information"):
            st.code(f"Error: {e}")
            st.info("Check your services with: `docker-compose ps`")

if __name__ == "__main__":
    main()
