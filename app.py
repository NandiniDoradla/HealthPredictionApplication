import re
from datetime import datetime
from flask import Flask, render_template, request, redirect
import sqlite3
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)
model = genai.GenerativeModel("gemini-2.5-flash")

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        dob TEXT NOT NULL,
        email TEXT NOT NULL,
        glucose REAL NOT NULL,
        haemoglobin REAL NOT NULL,
        cholesterol REAL NOT NULL,
        remarks TEXT
    )
    ''')

    conn.commit()
    conn.close()
def generate_health_remark(glucose, haemoglobin, cholesterol):

    prompt = f"""
    Patient Health Data:

    Glucose: {glucose}
    Haemoglobin: {haemoglobin}
    Cholesterol: {cholesterol}

    Predict possible health condition or disease risk.

    Give only a short medical remark in 1 sentence.
    """

    response = model.generate_content(prompt)

    return response.text

@app.route('/')
def home():

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients")

    patients = cursor.fetchall()

    conn.close()

    return render_template('index.html', patients=patients)

@app.route('/add', methods=['GET', 'POST'])
def add_patient():

    if request.method == 'POST':

        full_name = request.form['full_name']
        dob = request.form['dob']
        email = request.form['email']
        glucose = request.form['glucose']
        haemoglobin = request.form['haemoglobin']
        cholesterol = request.form['cholesterol']

        # Email Validation
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if not re.match(email_pattern, email):
            return "Invalid Email Address"

        # DOB Validation
        dob_date = datetime.strptime(dob, "%Y-%m-%d")

        if dob_date.date() > datetime.today().date():
            return "Date of Birth cannot be a future date"

        # Numeric Validation
        try:
            glucose = float(glucose)
            haemoglobin = float(haemoglobin)
            cholesterol = float(cholesterol)

        except ValueError:
            return "Glucose, Haemoglobin and Cholesterol must be numeric values"

        # Gemini AI Prediction
        remarks = generate_health_remark(
            glucose,
            haemoglobin,
            cholesterol
        )

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO patients
        (full_name,dob,email,glucose,haemoglobin,cholesterol,remarks)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            full_name,
            dob,
            email,
            glucose,
            haemoglobin,
            cholesterol,
            remarks
        ))

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('add_patient.html')
@app.route('/delete/<int:id>')
def delete_patient(id):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM patients WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/')
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':

        full_name = request.form['full_name']
        dob = request.form['dob']
        email = request.form['email']
        glucose = request.form['glucose']
        haemoglobin = request.form['haemoglobin']
        cholesterol = request.form['cholesterol']

        cursor.execute("""
        UPDATE patients
        SET full_name=?,
            dob=?,
            email=?,
            glucose=?,
            haemoglobin=?,
            cholesterol=?
        WHERE id=?
        """,
        (
            full_name,
            dob,
            email,
            glucose,
            haemoglobin,
            cholesterol,
            id
        ))

        conn.commit()
        conn.close()

        return redirect('/')

    cursor.execute(
        "SELECT * FROM patients WHERE id=?",
        (id,)
    )

    patient = cursor.fetchone()

    conn.close()

    return render_template(
        'edit_patient.html',
        patient=patient
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)