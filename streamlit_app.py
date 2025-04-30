
from google import genai
from google.genai import types
import streamlit as st

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import re
import requests
from io import StringIO

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.model_selection import train_test_split # Split data into train data and test data
from sklearn.metrics import r2_score, mean_squared_error # Metrics for Regression Analysis
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# Show title and description.
st.title("PickMyLaptop_Chatbot")
st.write(
    "This is a simple chatbot that uses Gemini flash 2.5 model to help users pick their preferred laptop. "
    "To use this app, you need to provide a Gemini API key, which you can get [here](https://ai.google.dev/gemini-api/docs/api-key). "
    "You can also learn how to build this app step by step by [following our tutorial](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management

def load_original_data():
    url = 'https://raw.githubusercontent.com/metrosmash/PickMyLaptop_ChatBot/refs/heads/main/Data/cleaned.csv'
    response = requests.get(url)
    if response.status_code == 200:
        return pd.read_csv(StringIO(response.text))
    else:
        st.error("Failed to load data from GitHub.")
        return None

data_f = load_original_data()
st.write(data_f.head())


Gemini_api_key = st.text_input("Gemini API Key", type="password")
if not Gemini_api_key:
    st.info("Please add your Gemini API Key to continue.", icon="🗝️")
else:

    # Create a Gemini API client.
    client = genai.Client(api_key=Gemini_api_key)


'''

    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("What is up?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate a response using the OpenAI API.
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )

        # Stream the response to the chat using `st.write_stream`, then store it in 
        # session state.
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

        '''
