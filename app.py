import streamlit as st
import openai
from transformers import pipeline
import pandas as pd
import streamlit_authenticator as stauth

# User authentication
names = ["John Doe", "Jane Doe"]
usernames = ["johndoe", "janedoe"]
passwords = ["password123", "password456"]

hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "chatbot_app", "abcdef", cookie_expiry_days=30)
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    # Change it to your OpenAI API key
    openai.api_key = 'KEY'

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
        coping_strategy = provide_coping_strategy(sentiment)
        
        response = generate_response(user_message)
        
        st.session_state['messages'].append(("Bot", response))
        st.session_state['mood_tracker'].append((user_message, sentiment, score))

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

    # Display coping strategies
    if submit_button and (user_message or selected_question):
        st.subheader("Suggested Coping Strategy")
        st.write(coping_strategy)

    # Display resources
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

    authenticator.logout("Logout", "sidebar")
elif authentication_status == False:
    st.error("Username/password is incorrect")
elif authentication_status == None:
    st.warning("Please enter your username and password")
