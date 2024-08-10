from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import openai
import pandas as pd
import sqlite3
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import os 
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for session management

# Download the VADER lexicon
nltk.download('vader_lexicon')

# Database setup
conn = sqlite3.connect('chatbot.db', check_same_thread=False)
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
openai_api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = openai_api_key  # Ensure this is your actual API key

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

# Home route to handle chat
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'messages' not in session:
        session['messages'] = []
    if 'mood_tracker' not in session:
        session['mood_tracker'] = []

    if request.method == 'POST':
        user_message = request.form['user_message']
        if user_message:
            session['messages'].append(("You", user_message))
            
            sentiment, score = analyze_sentiment(user_message)
            coping_strategy = provide_coping_strategy(sentiment)
            
            response = generate_response(user_message)
            
            session['messages'].append(("Bot", response))
            session['mood_tracker'].append((user_message, sentiment, score))

            # Store messages in the database
            c.execute("INSERT INTO messages (sender, message, sentiment, polarity) VALUES (?, ?, ?, ?)", 
                      ("You", user_message, sentiment, score))
            c.execute("INSERT INTO messages (sender, message) VALUES (?, ?)", 
                      ("Bot", response))
            conn.commit()

            return render_template('chatbot.html', messages=session['messages'], coping_strategy=coping_strategy)

    return render_template('chatbot.html', messages=session['messages'])

# Feedback route
@app.route('/feedback', methods=['POST'])
def feedback():
    feedback_message = request.form['feedback_message']
    rating = request.form['rating']
    if feedback_message:
        c.execute("INSERT INTO feedback (message, feedback, rating) VALUES (?, ?, ?)", 
                  (feedback_message, feedback_message, rating))
        conn.commit()
        return jsonify({"status": "success", "message": "Thank you for your feedback!"})

    return jsonify({"status": "failure", "message": "Feedback not submitted."})

# Resources route
@app.route('/resources')
def resources():
    resources = [
        "National Suicide Prevention Lifeline: 1-800-273-8255",
        "Crisis Text Line: Text 'HELLO' to 741741",
        "More Resources: https://www.mentalhealth.gov/get-help/immediate-help"
    ]
    return render_template('resources.html', resources=resources)

# Session summary route
@app.route('/session_summary')
def session_summary():
    return render_template('session_summary.html', mood_tracker=session.get('mood_tracker', []))

if __name__ == '__main__':
    app.run(debug=True)
