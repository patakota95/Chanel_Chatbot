import nest_asyncio
nest_asyncio.apply()  # Apply nest_asyncio to patch the event loop

import asyncio
import asyncpraw
import streamlit as st
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv  # Import python-dotenv
from google.generativeai import configure, GenerativeModel

# Custom CSS for styling
st.markdown(
    """
    <style>
    body {
        background-color: #f0f2f6;
        font-family: 'Segoe UI', sans-serif;
    }
    .header-banner {
        width: 100%;
        border-radius: 10px;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .chat-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .chat-message {
        margin-bottom: 10px;
        padding: 10px;
        border-radius: 5px;
    }
    .chat-message.user {
        background-color: #d1e7dd;
        text-align: right;
    }
    .chat-message.bot {
        background-color: #ffeeba;
        text-align: left;
    }
    </style>
    """, unsafe_allow_html=True
)

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variable
gemini_api_key = os.getenv("YOUR_GEMINI_API_KEY")
if not gemini_api_key:
    st.error("API key not found! Please check your .env file.")
else:
    # ---- Google Gemini AI Setup ----
    configure(api_key=gemini_api_key)
    gemini_model = GenerativeModel("gemini-2.0-flash")

# ---- Reddit API Setup ----
REDDIT_CLIENT_ID = "5vKQC9dHe6lK3dOajbHzYA"
REDDIT_CLIENT_SECRET = "z9Dszn2ZEs1LLAG4Ua4PE31Ft6rKyQ"
REDDIT_USER_AGENT = "fashionBot/0.1 (by u/patakotachaitanya)"

# Authenticate with Reddit API
reddit = asyncpraw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

# ---- Function to Fetch Reddit Posts ----
async def fetch_reddit_posts(keyword, subreddit="fashion", limit=50):
    """
    Fetch recent posts containing the given keyword from a subreddit.
    """
    posts = []
    # Await the subreddit object first
    sub = await reddit.subreddit(subreddit)
    async for submission in sub.search(keyword, sort="new", limit=limit):
        posts.append((submission.created_utc, submission.title, submission.selftext))
    return posts

# Wrapper to run async function synchronously using the current event loop
def fetch_reddit_posts_sync(keyword, subreddit="fashion", limit=50):
    return asyncio.get_event_loop().run_until_complete(
        fetch_reddit_posts(keyword, subreddit, limit)
    )

# ---- Function to Analyze Post Frequency ----
def count_post_mentions(posts):
    now = datetime.utcnow()
    return {
        "last_day": sum(1 for time, _, _ in posts if now - datetime.utcfromtimestamp(time) < timedelta(days=1)),
        "last_week": sum(1 for time, _, _ in posts if now - datetime.utcfromtimestamp(time) < timedelta(weeks=1)),
        "last_month": sum(1 for time, _, _ in posts if now - datetime.utcfromtimestamp(time) < timedelta(days=30))
    }

# ---- Gemini Chatbot ----
def chat_response(user_message):
    response = gemini_model.generate_content(user_message)
    return response.text if response else "I'm sorry, I couldn't generate a response."

# ---- Streamlit Chatbot Interface ----

# Display header banner image (replace with your preferred image URL)
st.image("https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1500&q=80", 
         caption="Fashion Trends", use_container_width=True, output_format="auto", clamp=True)

st.title("Fashion Trend Chatbot")
st.write("This chatbot fetches Reddit trends and answers your fashion-related queries with style!")

# Sidebar for Trend Analysis with a styled container
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.header("Trend Analysis")
    keyword = st.text_input("Enter a fashion keyword:")
    if st.button("Check Trend"):
        if keyword:
            posts = fetch_reddit_posts_sync(keyword, subreddit="fashion", limit=50)
            counts = count_post_mentions(posts)
            
            st.write("**Mentions in the last:**")
            st.write(f"- **Day:** {counts['last_day']}")
            st.write(f"- **Week:** {counts['last_week']}")
            st.write(f"- **Month:** {counts['last_month']}")
            
            if posts:
                with st.expander("See Sample Posts"):
                    for post_time, post_title, _ in posts[:5]:
                        st.write(f"- **{datetime.utcfromtimestamp(post_time).strftime('%Y-%m-%d %H:%M:%S')}**: {post_title}")
        else:
            st.write("Please enter a keyword.")
    st.markdown('</div>', unsafe_allow_html=True)

# Main Chatbot Section with a container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
st.subheader("Chat with the Fashion Bot")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("Your message:")
if st.button("Send") and user_input:
    bot_response = chat_response(user_input)
    st.session_state.chat_history.append(("You", user_input))
    st.session_state.chat_history.append(("Bot", bot_response))

# Display chat history with styled messages
for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.markdown(f'<div class="chat-message user"><strong>{sender}:</strong> {message}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message bot"><strong>{sender}:</strong> {message}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)