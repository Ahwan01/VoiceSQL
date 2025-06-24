from dotenv import load_dotenv
import streamlit as st
import os
import sqlite3
import google.generativeai as gi
import speech_recognition as sr

# Load environment variables
load_dotenv()


api_key = os.getenv("GOOGLE-API-KEY")
if not api_key:
    st.error("API Key is missing. Please set your GOOGLE-API-KEY in .env file.")
gi.configure(api_key=api_key)

# Gemini Model Setup
def get_gemini_response(question, prompt):
    try:
        # model = gi.GenerativeModel('models/gemini-1.5-pro-latest')
        model = gi.GenerativeModel('models/gemini-2.0-flash-lite')
        response = model.generate_content([prompt[0], question])
        sql_query = response.text.strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        # Log generated SQL query
        
        return sql_query
    except Exception as e:
        st.error(f"Error generating SQL query: {e}")
        return None

# Database Query Execution
def read_sql_query(sql, db):
    try:
        with sqlite3.connect(db) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            return rows
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []

# Speech Recognition
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            st.error("Could not understand the audio.")
        except sr.RequestError:
            st.error("Error with the speech recognition service.")
    return ""

# SQL Query Prompt
prompt = [
    """
    You are an expert in converting English questions to SQL queries!
    The SQL database is named STUDENT and has columns - NAME, CLASS, SECTION, MARKS.
    
    Examples:
    1. "How many student records exist?"
       SQL: SELECT COUNT(*) FROM STUDENT;
    2. "Show all students in Data Science class."
       SQL: SELECT * FROM STUDENT WHERE CLASS='Data Science';
    3. "Who scored the highest marks?"
       SQL: SELECT NAME FROM STUDENT ORDER BY MARKS DESC LIMIT 1;
    4. "get viveks dta or get data of student nmed Vivek"
        SQL:SELECT * FROM STUDENT WHERE NAME='Vivek';
    
    The output should not contain ``` or any explanation, just the SQL query.and take the first letter of all data in UPPERCASE.For Example if the input is 'vivek' it should take it as 'Vivek'
    """
]

# Streamlit App UI
st.set_page_config(page_title="VoiceSQL: Speak & Retrieve Data")
st.title("🎙️ VoiceSQL: Convert Speech to SQL Queries")
st.write("Ask a question, and I will fetch data!")

# Initialize session state for persistence
if "question" not in st.session_state:
    st.session_state.question = ""

# User Input
text_input = st.text_input("Type your question here:", key="input")

# Speech Recognition Button
if st.button("🎤 Speak Now"):
    spoken_text = recognize_speech()
    if spoken_text:
        st.session_state.question = spoken_text
        st.write(f"Recognized: {spoken_text}")

# Ensure latest input is stored
if text_input:
    st.session_state.question = text_input

final_question = st.session_state.question

# SQL Query Generation & Execution
if st.button("🔍 Get Data") and final_question:
    sql_query = get_gemini_response(final_question, prompt)
    if sql_query:
        results = read_sql_query(sql_query, "student.db")
        
        # Display Results
        st.subheader("Results:")
        if results:
            for row in results:
                st.write(row)
        else:
            st.write("No matching records found.")
    
    # Clear stored question
    st.session_state.question = ""
