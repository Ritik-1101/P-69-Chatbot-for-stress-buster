import streamlit as st
import openai
from transformers import pipeline
import pandas as pd
import streamlit_authenticator as stauth
import sqlite3
import requests
import matplotlib.pyplot as plt

# User authentication
names = ["John Doe", "Jane Doe"]
usernames = ["johndoe", "janedoe"]
passwords = ["password123", "password456"]

hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "chatbot_app", "abcdef", cookie_expiry_days=30)
name, authentication_status, username = authenticator.login("Login", "main")

# Database setup
conn = sqlite3.connect('chatbot.db')
c = conn.cursor()

# Create tables if they do not exist
c.execute('''
CREATE TABLE IF NOT EXISTS messages (
    username TEXT,
    sender TEXT,
    message TEXT,
    sentiment TEXT,
    polarity REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS feedback (
    username TEXT,
    message TEXT,
    feedback TEXT,
    rating INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()

if authentication_status:
    # Change it to your OpenAI API key
    openai.api_key = 'YOUR_OPENAI_API_KEY'

    # Function to generate a response from GPT-3.5-turbo
    def generate_response(prompt):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response['choices'][0]['message']['content'].strip()
        except openai.error.OpenAIError as e:
            return f"An error occurred: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    # Initialize sentiment analysis model
    sentiment_analysis = pipeline("sentiment-analysis")

    # Analyze sentiment
    def analyze_sentiment(text):
        result = sentiment_analysis(text)[0]
        label = result['label']
        score = result['score']
        if label == 'POSITIVE' and score > 0.75:
            return "Very Positive", score
        elif label == 'POSITIVE' and score > 0.5:
            return "Positive", score
        elif label == 'NEGATIVE' and score > 0.75:
            return "Very Negative", score
        elif label == 'NEGATIVE' and score > 0.5:
            return "Negative", score
        else:
            return "Neutral", score

    # Provide coping strategies
    def provide_coping_strategy(sentiment, user_history):
        strategies = {
            "Very Positive": "Keep up the positive vibes! Consider sharing your good mood with others.",
            "Positive": "It's great to see you're feeling positive. Keep doing what you're doing!",
            "Neutral": "Feeling neutral is okay. Consider engaging in activities you enjoy.",
            "Negative": "It seems you're feeling down. Try to take a break and do something relaxing.",
            "Very Negative": "I'm sorry to hear that you're feeling very negative. Consider talking to a friend or seeking professional help."
        }
        # Personalize based on user history
        if sentiment in user_history:
            strategies["Positive"] += " Remember last time you enjoyed a walk in the park?"
        return strategies.get(sentiment, "Keep going, you're doing great!")

    # Integrate with external APIs for more resources
    def get_external_resources():
        try:
            response = requests.get("https://api.mentalhealth.com/resources")
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except requests.exceptions.RequestException as e:
            return f"An error occurred: {str(e)}"

    # Streamlit app layout
    st.title("Mental Health Support Chatbot")

    # Add custom CSS
    st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
        font-family: Arial, sans-serif;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .stTextInput>div>input {
        border: 2px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'mood_tracker' not in st.session_state:
        st.session_state['mood_tracker'] = []
    if 'user_history' not in st.session_state:
        st.session_state['user_history'] = []

    # Load previous chat history
    c.execute("SELECT sender, message FROM messages WHERE username=? ORDER BY timestamp", (username,))
    rows = c.fetchall()
    st.session_state['messages'] = [(row[0], row[1]) for row in rows]

    # Pre-defined questions
    predefined_questions = ["How are you feeling today?", "Do you want to talk about your day?", "Is there something bothering you?"]

    # Chat input form
    with st.form(key='chat_form'):
        user_message = st.text_input("You:", placeholder="Type your message here or select a question below...")
        selected_question = st.selectbox("Or select a pre-defined question:", [""] + predefined_questions)
        submit_button = st.form_submit_button(label='Send')

    # Handle form submission
    if submit_button and (user_message or selected_question):
        if selected_question:
            user_message = selected_question

        st.session_state['messages'].append(("You", user_message))
        
        sentiment, score = analyze_sentiment(user_message)
        coping_strategy = provide_coping_strategy(sentiment, st.session_state['user_history'])
        
        response = generate_response(user_message)
        
        st.session_state['messages'].append(("Bot", response))
        st.session_state['mood_tracker'].append((user_message, sentiment, score))
        st.session_state['user_history'].append(sentiment)

        # Store messages in the database
        c.execute("INSERT INTO messages (username, sender, message, sentiment, polarity) VALUES (?, ?, ?, ?, ?)", 
                  (username, "You", user_message, sentiment, score))
        c.execute("INSERT INTO messages (username, sender, message) VALUES (?, ?, ?)", 
                  (username, "Bot", response))
        conn.commit()

    # Display chat messages
    st.subheader("Chat")
    for sender, message in st.session_state['messages']:
        if sender == "You":
            st.markdown(f"**You:** {message}")
        else:
            st.markdown(f"**Bot:** {message}")

    # Display mood tracking chart
    if st.session_state['mood_tracker']:
        st.subheader("Mood Tracking")
        mood_data = pd.DataFrame(st.session_state['mood_tracker'], columns=["Message", "Sentiment", "Score"])
        st.line_chart(mood_data['Score'])

        # Additional visualizations
        st.subheader("Advanced Visualizations")
        fig, ax = plt.subplots()
        mood_data['Sentiment'].value_counts().plot(kind='bar', ax=ax, title='Sentiment Distribution')
        st.pyplot(fig)

        fig, ax = plt.subplots()
        mood_data.groupby('Sentiment')['Score'].mean().plot(kind='pie', autopct='%1.1f%%', ax=ax, title='Average Sentiment Scores')
        st.pyplot(fig)

    # Display coping strategies
    if submit_button and (user_message or selected_question):
        st.subheader("Suggested Coping Strategy")
        st.write(coping_strategy)

    # Display feedback form
    st.subheader("Feedback")
    with st.form(key='feedback_form'):
        feedback_message = st.text_area("Feedback on the last response:")
        rating = st.slider("Rate the response", 1, 5, 3)
        submit_feedback_button = st.form_submit_button(label='Submit Feedback')

    if submit_feedback_button and feedback_message:
        c.execute("INSERT INTO feedback (username, message, feedback, rating) VALUES (?, ?, ?, ?)", 
                  (username, feedback_message, feedback_message, rating))
        conn.commit()
        st.success("Thank you for your feedback!")

    # Display resources from external API
    st.sidebar.title("Resources")
    resources = get_external_resources()
    if resources:
        for resource in resources:
            st.sidebar.write(f"{resource['name']}: {resource['contact']}")
    else:
        st.sidebar.write("No additional resources available at the moment.")

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

    authenticator.logout("Logout", "sidebar")
elif authentication_status == False:
    st.error("Username/password is incorrect")
elif authentication_status == None:
    st.warning("Please enter your username and password")
