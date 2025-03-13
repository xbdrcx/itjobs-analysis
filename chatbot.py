from app import fetch_all_jobs
from transformers import pipeline
import speech_recognition as sr
import streamlit as st
import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Initialize the language model
chatbot = pipeline('text-generation', model='gpt2', device=device)

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Function to recognize speech
def recognize_speech():
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Sorry, I did not understand that."
        except sr.RequestError:
            return "Could not request results; check your network connection."

# Streamlit UI
st.title("IT Job Market Chatbot")

# Display chat history
if 'history' not in st.session_state:
    st.session_state.history = []

for chat in st.session_state.history:
    st.write(chat)

# User input
user_input = st.text_input("You:")

# Speech input
if st.button("Speak"):
    user_input = recognize_speech()
    st.write(f"You: {user_input}")

# Generate response
if user_input:
    job_data = fetch_all_jobs()

    # Limit the job data to avoid too large input
    limited_job_data = job_data[:500] if len(job_data) > 500 else job_data
    bot_input = f"User asked about IT job market. Job data: {limited_job_data}"

    try:
        response = chatbot(bot_input, max_new_tokens=50)
        if response and len(response) > 0:
            bot_response = response[0].get('generated_text', "I'm not sure how to respond.")
        else:
            bot_response = "I'm not sure how to respond."
    except Exception as e:
        bot_response = f"Error generating response: {e}"

    st.session_state.history.append(f"You: {user_input}")
    st.session_state.history.append(f"Bot: {bot_response}")
    st.write(f"Bot: {bot_response}")
