
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
st.write("this is the test_app for the main_streamlit app (having problems running it locally )")


# mysql database connection.
# Retrieve database credentials from Streamlit secrets
db_username = st.secrets["DB_username"]
db_password = st.secrets["DB_password"]
#Api_key = st.secrets["API_key"]

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

except mysql.connector.Error as e:
    # Print an error message if a connection error occurs
    st.write(e)


cursor = conn.cursor()
query = "SELECT * FROM laptop_dataset WHERE 1 "
cursor.execute(query)
results = cursor.fetchall()
st.write(results)

#This function is the only function for now the agent will be able to extract information fron the database with this function
def execute_query(sql: str) -> list[list[str]]:
    """Execute an SQL statement, returning the results."""
    print(f' - DB CALL: execute_query({sql})')

    cursor = conn.cursor()

    cursor.execute(sql)
    return cursor.fetchall()


st.write(execute_query("SELECT * FROM laptop_dataset WHERE 1 "))
