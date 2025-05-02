
from google import genai
from google.genai import types
import streamlit as st
import pymysql
import pymysql.cursors

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import re
import requests
from io import StringIO


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

db_username = st.secrets["DB_username"]
db_password = st.secrets["DB_password"]
# host ="localhost:3306"

conn = pymysql.connect(
    host ="localhost",
    user = db_username,
    password = db_password,
    database = "laptop_datadb",
    cursorclass=pymysql.cursors.DictCursor
    )
cursor = conn.cursor()

create_table_query = """
    CREATE TABLE IF NOT EXISTS Laptop (
    id INT PRIMARY KEY AUTO_INCREMENT,
    Brand TEXT,
    Product_Description TEXT,
    Screen_Size TEXT,
    RAM FLOAT, 
    Processor TEXT,
    GPU TEXT,
    GPU_Type TEXT,
    Resolution TEXT,
    Condition1 TEXT,
    Price FLOAT,
    SSD INTEGER,
    HDD INTEGER
)
    """
cursor.execute(create_table_query)
conn.commit()


api_key = st.secrets["API_key"]

# Initialize connection.
conn = st.connection('mysql', type='sql')

# Perform query.
df = conn.query('SELECT * from mytable;', ttl=600)

# Print results.
for row in df.itertuples():
    st.write(f"{row.name} has a :{row.pet}:")

def load_original_data():
    url = 'https://raw.githubusercontent.com/metrosmash/PickMyLaptop_ChatBot/refs/heads/main/Data/laptop_dataset.csv'
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



