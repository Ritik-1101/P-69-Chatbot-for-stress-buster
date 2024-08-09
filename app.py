import streamlit as st
import openai
import pandas as pd
import sqlite3
import requests
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Download the VADER lexicon
nltk.download('vader_lexicon')

# Database setup
conn = sqlite3.connect('chatbot.db')
c = conn.cursor()

# Create tables if they do not exist
c.execute('''
CREATE TABLE IF NOT EXISTS messages (
    sender TEXT,
    message TEXT,
    sentiment TEXT,
    polarity REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS feedback (
    message TEXT,
    feedback TEXT,
    rating INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()

# Set your OpenAI API key
openai.api_key = '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'  # Ensure this is your actual API key

# Function to generate a response from GPT-3.5-turbo
def generate_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except openai.error.AuthenticationError:
        return "Invalid API key provided."
    except openai.error.OpenAIError as e:
        return f"An error occurred: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# Initialize sentiment analysis model
vader = SentimentIntensityAnalyzer()

# Analyze sentiment
def analyze_sentiment(text):
    result = vader.polarity_scores(text)
    score = result['compound']
    if score >= 0.5:
        return "Very Positive", score
    elif 0.1 <= score < 0.5:
        return "Positive", score
    elif -0.1 < score < 0.1:
        return "Neutral", score
    elif -0.5 < score <= -0.1:
        return "Negative", score
    else:
        return "Very Negative", score

# Provide coping strategies
def provide_coping_strategy(sentiment):
    strategies = {
        "Very Positive": "Keep up the positive vibes! Consider sharing your good mood with others.",
        "Positive": "It's great to see you're feeling positive. Keep doing what you're doing!",
        "Neutral": "Feeling neutral is okay. Consider engaging in activities you enjoy.",
        "Negative": "It seems you're feeling down. Try to take a break and do something relaxing.",
        "Very Negative": "I'm sorry to hear that you're feeling very negative. Consider talking to a friend or seeking professional help."
    }
    return strategies.get(sentiment, "Keep going, you're doing great!")

# Streamlit app layout
st.title("Mental Health Support Chatbot")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'mood_tracker' not in st.session_state:
    st.session_state['mood_tracker'] = []

# Chat input form
user_message = st.text_input("You:", placeholder="Type your message here...")
submit_button = st.button(label='Send')

# Handle form submission
if submit_button and user_message:
    st.session_state['messages'].append(("You", user_message))
    
    sentiment, score = analyze_sentiment(user_message)
    coping_strategy = provide_coping_strategy(sentiment)
    
    response = generate_response(user_message)
    
    st.session_state['messages'].append(("Bot", response))
    st.session_state['mood_tracker'].append((user_message, sentiment, score))

    # Store messages in the database
    c.execute("INSERT INTO messages (sender, message, sentiment, polarity) VALUES (?, ?, ?, ?)", 
              ("You", user_message, sentiment, score))
    c.execute("INSERT INTO messages (sender, message) VALUES (?, ?)", 
              ("Bot", response))
    conn.commit()

# Display chat messages
st.subheader("Chat")
for sender, message in st.session_state['messages']:
    st.write(f"**{sender}:** {message}")

# Display mood tracking chart
if st.session_state['mood_tracker']:
    st.subheader("Mood Tracking")
    mood_data = pd.DataFrame(st.session_state['mood_tracker'], columns=["Message", "Sentiment", "Score"])
    st.line_chart(mood_data['Score'])

# Display coping strategies
if submit_button and user_message:
    st.subheader("Suggested Coping Strategy")
    st.write(coping_strategy)

# Display feedback form
st.subheader("Feedback")
feedback_message = st.text_area("Feedback on the last response:")
rating = st.slider("Rate the response", 1, 5, 3)
submit_feedback_button = st.button(label='Submit Feedback')

if submit_feedback_button and feedback_message:
    c.execute("INSERT INTO feedback (message, feedback, rating) VALUES (?, ?, ?)", 
              (feedback_message, feedback_message, rating))
    conn.commit()
    st.success("Thank you for your feedback!")

# Display resources from external API
st.sidebar.title("Resources")
st.sidebar.write("If you need immediate help, please contact one of the following resources:")
st.sidebar.write("1. National Suicide Prevention Lifeline: 1-800-273-8255")
st.sidebar.write("2. Crisis Text Line: Text 'HELLO' to 741741")
st.sidebar.write("[More Resources](https://www.mentalhealth.gov/get-help/immediate-help)")

# Display session summary
if st.sidebar.button("Show Session Summary"):
    st.sidebar.subheader("Session Summary")
    for i, (message, sentiment, score) in enumerate(st.session_state['mood_tracker']):
        st.sidebar.write(f"{i+1}. **Message:** {message}")
        st.sidebar.write(f"**Sentiment:** {sentiment} (Score: {score})")
        st.sidebar.write("---")
