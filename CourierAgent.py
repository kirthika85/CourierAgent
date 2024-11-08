import streamlit as st
import pandas as pd
import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import logging

load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
csv_location = "courier_rates.csv"

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

def df_to_json(csv_location):
    df = pd.read_csv(csv_location)
    return df

# Define a function to interact with OpenAI, including chat history and shipment data
def query_openai(client, prompt, df):
    markdown_str = df.to_markdown(tablefmt="grid")
    messages = [{"role": "system", "content": "You are a helpful courier assistant."}]
    
    for message in st.session_state["chat_history"]:
        messages.append({"role": message["role"], "content": message["content"]})

    messages.append({"role": "system", "content": f"""
                 You are given with a table of actual data which includes start location Zipcode, destination or end Zipcode, weight (in lbs), height, width, length in cms and cost in dollars.
                  You can ask questions to the user interactively with appropriate units, until you get all the relevant information from the user.
                  Do not expect the user to provide all details at one shot.
                  Change questions based on the received input. Check and provide the cost with the help of the data available with you. Do not calculate any rates at this moment.
                  Once you have collected all the data from the user, check the given Actual data to get the cost for the given Zipcodes, weights and dimensions and respond with the cost.
                  If any question is asked apart from the scope of courier services, say, 'I am sorry, this is not relevant to the context. Kindly ask a valid question.' 
                  \n Actual data:{markdown_str}"""})
    messages.append({"role": "user", "content": prompt})
                
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.2
    )
    answer = response.choices[0].message.content
    return answer

client = OpenAI(api_key=OPENAI_API_KEY)
df = df_to_json(csv_location)

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
    on_change=clear_input  # Callback to clear input
)

if user_input:
    with st.spinner("Fetching response..."):
        answer = query_openai(client, user_input, df)
        
        # Update chat history
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        st.session_state["chat_history"].append({"role": "assistant", "content": answer})
        
        render_chat()
