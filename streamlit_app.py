
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


def query_sql_database(query: str):
    conn = None
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host="db4free.net",
            user=db_username,
            password=db_password,
            database="metro_laptop"
        )

        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

            # Get column names
            columns = [i[0] for i in cursor.description]

            # Return as a DataFrame (or you could return list of dicts)
            df = pd.DataFrame(results, columns=columns)

            return df  # Let the AI agent process the DataFrame

    except mysql.connector.Error as e:
        # Return error message instead of raising
        return {"error": str(e)}

    finally:
        # Always clean up
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()


result = query_sql_database("SELECT * FROM laptop_dataset LIMIT 5;")

st.write(result)
