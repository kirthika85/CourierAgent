import streamlit as st
import pandas as pd
import os
import openai
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set API key
openai.api_key = os.getenv("OPENAI_API_KEY")
csv_location = "courier_rates.csv"

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Load CSV data
def load_dataframe(csv_location):
    df = pd.read_csv(csv_location)
    return df

# Define function to interact with OpenAI API
def query_openai(prompt, df):
    markdown_str = df.to_markdown(tablefmt="grid")
    messages = [{"role": "system", "content": "You are a helpful courier assistant."}]

    for message in st.session_state["chat_history"]:
        messages.append({"role": message["role"], "content": message["content"]})

    messages.append({"role": "system", "content": f"""
        You are given a table of data which includes start location Zipcode, destination Zipcode, weight (in lbs), height, width, length in cms, and cost in dollars.
        Ask questions to gather relevant information and use the table to respond with the cost.
        If asked irrelevant questions, respond appropriately. Actual data:\n{markdown_str}
    """})
    messages.append({"role": "user", "content": prompt})
                
    # Ensure correct model name and API call
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.2
        )
        answer = response.choices[0].message['content']
        logger.debug("OpenAI response: %s", answer)
        return answer
    except Exception as e:
        logger.error("Error with OpenAI API call: %s", e)
        return "There was an error fetching the response. Please try again later."

# Load data
df = load_dataframe(csv_location)

# Streamlit UI setup
st.title("Courier Agent")
st.write("I am a Smart Courier Agent! How can I help you?")

chat_container = st.empty()

def render_chat():
    chat_content = ""
    for message in st.session_state["chat_history"]:
        if message["role"] == "user":
            chat_content += f"**You:** {message['content']}\n\n"
        else:
            chat_content += f"**Courier Agent:** {message['content']}\n\n"
    chat_container.markdown(chat_content, unsafe_allow_html=True)

render_chat()

# Define a function to clear the input field after submission
def clear_input():
    st.session_state["user_input"] = ""

# Set up text input with a callback to clear it after submission
user_input = st.text_input(
    "Enter your question:", 
    placeholder=" (e.g., 'I want to send courier from Zipcode 00926 to 11368. I need to know the amount.')",
    key="user_input",
    on_change=clear_input
)

if user_input:
    with st.spinner("Fetching response..."):
        answer = query_openai(user_input, df)
        
        # Update chat history
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        st.session_state["chat_history"].append({"role": "assistant", "content": answer})
        
        render_chat()
