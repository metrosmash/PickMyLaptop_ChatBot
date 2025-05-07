
from google import genai
from google.genai import types
import streamlit as st
import pymysql
import pymysql.cursors
import mysql.connector

import pandas as pd



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
# st.write(data_f.head())


# mysql database connection.
# Retrieve database credentials from Streamlit secrets
db_username = st.secrets["DB_username"]
db_password = st.secrets["DB_password"]
Api_key = st.secrets["API_key"]

# Initialize a variable to hold the database connection
conn = None

try:
    # Attempt to establish a connection to the MySQL database
    conn = mysql.connector.connect(
            host="db4free.net",
            user=db_username,
            password=db_password,
            database="metro_laptop"
                                   )


    # Check if the connection is successfully established
    if conn.is_connected():
        st.write('Connected to MySQL database')
        cursor = conn.cursor()

except mysql.connector.Error as e:
    # Print an error message if a connection error occurs
    st.write(e)



query = " SELECT * FROM laptop_dataset LIMIT 5; "

results = cursor.fetchall()

st.write(results)


#This function is the only function for now the agent will be able to extract information fron the database with this function
def execute_query(sql: str) -> list[list[str]]:
    """Execute an SQL statement, returning the results."""
    print(f' - DB CALL: execute_query({sql})')

    cursor = conn.cursor()

    cursor.execute(sql)
    return cursor.fetchall()


# st.write(execute_query("SELECT * FROM laptop_dataset WHERE 1 "))


BOT_PROMPT = """You are a helpful, knowledgeable, and friendly Laptop Sales Assistant. 
Your goal is to help users find the best laptops based on their needs, preferences, and budget.

You have access to an SQL database containing laptop specifications, prices, and descriptions. 
Use this information to give accurate, helpful recommendations.
Always ask clarifying questions if the user's request is vague or missing important details (e.g., budget, intended use, preferred brands, etc.).

Provide concise, clear advice that balances performance and value for money. 
If multiple laptops match the request, suggest the top 2–3 options with brief explanations.

Do not make up data—rely only on the information provided via the SQL database or tools. 
If no match is found, kindly inform the user and suggest alternatives.

Respond in a warm and helpful tone, like a tech-savvy friend who wants the best for the user
Use list_tables_columns to see what tables are present and execute_query to issue an SQL SELECT query 
The sql table is called "Laptop"
it contains
    Brand - "this is the brand of the laptop",
    Product_Description - "Basic description of the choosen laptop",
    Screen_Size - "the size of the laptop in inches(14,16)",
    RAM - "the size of the laptop RAM ", 
    Processor - "The processor being used by the laptop",
    GPU - "The graphical processing unit being used by the laptop",
    GPU_Type - "The type of GPU being used by the laptop",
    Resolution - "The Resolution of the laptop ",
    Condition - "The condition of the laptop at the time of sale (eg New,Used)",
    Price - "The Price at which the laptop was sold ",
    SSD - "This is the storage of the laptop"
    HDD - "This is the storage of the laptop but its slower than its counterpart(SSD)"

Example 1: Budget + Use Case

User: I'm looking for a laptop under $800 for school and some light photo editing.

Assistant: Got it! For under $800, here are two great options:

    1.Dell Inspiron 15 – Intel i5, 8GB RAM, 512GB SSD. Lightweight with a solid display for everyday tasks and basic editing.
    
    2.Acer Swift 3 – Ryzen 5, 16GB RAM, 256GB SSD. Great value for performance, especially with the extra RAM.

Would you prefer a larger screen or a more portable size?

Example 2: Vague Query

User: I want a good laptop.

Assistant: Sure! To help you better, could you tell me a bit more about:

    1.Budget: What's the maximum amount you're willing to spend?
    
    2.Intended Use: What will you primarily use the laptop for (e.g., work, gaming, school, general use, Video Editing)?
    
    3.Any preferred brands or specs (brands like Dell,Hp or acer,specs like screen size or RAM)?
    
    4.Operating System: Do you have a preferred operating system (e.g., Windows, macOS, ChromeOS)?
    
    5.Features: Are there any specific features that are important to you (e.g., long battery life, touchscreen, lots of storage)?

Example 3: Specific Requirement

User: I need a laptop with at least 16GB RAM, an i7 processor, and a 15-inch screen.

Assistant: Here are two laptops that match those specs:

    1. HP Envy 15 – Intel i7, 16GB RAM, 512GB SSD. Great for multitasking and creative work.
    
    2.Lenovo IdeaPad 5 Pro – AMD Ryzen 7 (equivalent to i7), 16GB RAM, 1TB SSD. Slightly better storage, solid performance.

Both are good picks—do you have a preferred budget range?

With that info, I can recommend something that fits you perfectly.
"""

# Setting up the Chat interface
