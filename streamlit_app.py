
from google import genai
from google.genai import types
import streamlit as st
import pymysql
import pymysql.cursors
import mysql.connector

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

# loading the dataset
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


# mysql database connection.
# Retrieve database credentials from Streamlit secrets
db_username = st.secrets["DB_username"]
db_password = st.secrets["DB_password"]

# Initialize a variable to hold the database connection
conn = None

try:
    # Attempt to establish a connection to the MySQL database
    conn = mysql.connector.connect(
            host ="db4free.net",
            user = db_username,
            password = db_password,
            database = "metro_laptop"
                                   )

    # Check if the connection is successfully established
    if conn.is_connected():
        st.write('Connected to MySQL database')

except mysql.connector.Error as e:
    # Print an error message if a connection error occurs
    st.write(e)

# finally:
#     # Close the database connection in the 'finally' block to ensure it happens
#     if conn is not None and conn.is_connected():
#         conn.close()


# Insert the laptop_sales data into the sql database
for _, row in data_f.iterrows():
    conn.execute("INSERT INTO Laptop (Brand, Product_Description, Screen_Size, RAM, Processor, GPU, GPU_Type, Resolution, Condition1, Price, SSD, HDD) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (row['Brand'], row['Product_Description'], row['Screen_Size'], row['RAM'], row['Processor'], row['GPU'], row['GPU_Type'], row['Resolution'], row['Condition1'], row['Price'], row['SSD'], row['HDD']))

conn.commit()

conn.excecute("SELECT * FROM Laptop WHERE id = 3")
"""
cursor = conn.cursor()



api_key = st.secrets["API_key"]


Gemini_api_key = st.text_input("Gemini API Key", type="password")
if not Gemini_api_key:
    st.info("Please add your Gemini API Key to continue.", icon="🗝️")
else:

    # Create a Gemini API client.
    client = genai.Client(api_key=Gemini_api_key)

"""