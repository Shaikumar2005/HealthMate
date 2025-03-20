from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import google.generativeai as genai
from flask import send_file
import pandas as pd
import json
import os

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# Configure Google Generative AI
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["myDatabase"]
users_collection = db["Users"]

# Home route (renders frontend form)
@app.route("/")
def index():
    return render_template("details.html")

# Signup Route
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    full_name = data.get("fullName")
    age = data.get("age")
    gender = data.get("gender")
    email = data.get("email")
    phone_number = data.get("phoneNumber")
    password = data.get("password")

    if users_collection.find_one({"email": email}):
        return jsonify({"message": "Email already exists"}), 400

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({
        "fullName": full_name,
        "age": age,
        "gender": gender,
        "email": email,
        "phoneNumber": phone_number,
        "password": hashed_password
    })

    return jsonify({"message": "Signup successful"}), 201

# Login Route
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    
    user = users_collection.find_one({"email": email})
    
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"message": "Invalid email or password"}), 401
    
    return jsonify({"message": "Login successful"}), 200

# Function to generate a personalized health report
def generate_personalized_report(data):
    prompt = f"""
    Given the following health report data, generate a detailed personalized health recommendation:
    {data}
    The report should include key insights, improvement suggestions, and health risk analysis.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(prompt)

        if response and response.text:
            return response.text
        else:
            return "AI response was empty."
    except google.api_core.exceptions.ResourceExhausted:
        return "API quota exceeded. Please try again later or upgrade your quota."
    except Exception as e:
        return f"Error generating AI report: {str(e)}"

# Upload CSV/JSON and Generate Report
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            data = df.to_dict(orient='records')
        elif file.filename.endswith('.json'):
            data = json.load(file.stream)
        else:
            return jsonify({"error": "Invalid file format. Upload CSV or JSON only."}), 400

        report = generate_personalized_report(data)
        return jsonify({"personalized_report": report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#data collection
@app.route("/submit", methods=["POST"])
def submit():
    try:
        data = request.json
        if not data:
            return jsonify({"message": "No data received"}), 400  # Handle empty request

        # Validate required fields
        required_fields = ["name", "age", "weight", "height", "blood_pressure", "cholesterol", "sugar_level"]
        for field in required_fields:
            if field not in data or not data[field]:  # Check missing/empty fields
                return jsonify({"message": f"Missing or empty field: {field}"}), 400

        # Insert data into MongoDB
        users_collection.insert_one(data)

        return jsonify({"message": "Data submitted successfully!"}), 201  # HTTP 201 for created
    except Exception as e:
        print("Error:", e)  # Log error
        return jsonify({"message": "Internal Server Error"}), 500




import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from bson import ObjectId

def serialize_mongo_document(document):
    """Converts MongoDB document's ObjectId to string."""
    if document and "_id" in document:
        document["_id"] = str(document["_id"])
    return document

# ✅ Route to Generate Health Report
@app.route("/generate_report", methods=["GET"])
def generate_report():
    try:
        logging.info("Received request to generate report.")

        # Fetch latest data from MongoDB
        latest_data = users_collection.find_one(sort=[("_id", -1)])
        if not latest_data:
            logging.warning("No user data found in the database.")
            return jsonify({"message": "No user data found!"}), 404

        # Convert ObjectId to string
        latest_data = serialize_mongo_document(latest_data)

        # Generate personalized report using Gemini API
        report_text = generate_personalized_report(latest_data)

        # Combine user data with Gemini's analysis
        final_report = {
            "user_data": latest_data,
            "personalized_report": report_text
        }

        logging.info("Report successfully generated.")

        # ✅ Return JSON instead of a file
        return jsonify(final_report)

    except Exception as e:
        logging.error(f"Error generating report: {e}", exc_info=True)
        return jsonify({"message": "Error generating report"}), 500

# ✅ Chatbot Route

# Configure Gemini API (Make sure you have set up the API key)
genai.configure(api_key="AIzaSyBiudb7oc_VXiP_8iJal7mSCnMimBwzfd4")

def get_medical_response(user_message):
    """Fetches a short medical response from Gemini AI"""
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        
        # Use a system prompt to make responses short and medically focused
        prompt = f"""
        You are a medical assistant. Provide a **short, medically accurate** response to the following query.
        Avoid unnecessary conversational elements. Respond in **1-2 sentences max**.
        
        **User Query:** {user_message}
        """

        response = model.generate_content(prompt)

        # Extract response text and ensure it's concise
        reply = response.text.strip() if response.text else "I'm unable to provide an answer at the moment."
        return reply[:150]  # Ensure the response is short
    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/chat", methods=["POST"])
def chat():
    """Handles user messages and returns a short medical response"""
    user_message = request.json.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please enter a valid message!"})

    reply = get_medical_response(user_message)
    return jsonify({"reply": reply})


# Run Flask app
if __name__ == "__main__":
    app.run(debug=True, port=5000)