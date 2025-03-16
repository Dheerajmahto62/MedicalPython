from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import datetime

import os
import jwt

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# MongoDB Configuration (MongoDB Atlas)
app.config["MONGO_URI"] = "mongodb+srv://dheerajkumarmahto794:Dhiraj#62@medicalhealth.oywc4.mongodb.net/blood_donation?retryWrites=true&w=majority"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_secret_key")

# Initialize MongoDB & Extensions
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# MongoDB Collections
donors_collection = mongo.db.donors
camps_collection = mongo.db.camps

# Register Donor API
@app.route('/register_donor', methods=['POST'])
def register_donor():
    try:
        data = request.json
        print(f"Registering donor: {data}")

        required_fields = [
            "name", "age", "gender", "blood_group", "contact", "email",
            "password", "address", "eligible_next_donation", "preferred_location", "donor_status"
        ]

        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"message": "Missing required fields", "missing_fields": missing_fields}), 400

        if donors_collection.find_one({"email": data["email"]}):
            return jsonify({"message": "Email already registered"}), 409

        hashed_password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')

        donor = {
            "name": data["name"],
            "age": int(data["age"]),
            "gender": data["gender"],
            "blood_group": data["blood_group"],
            "contact": data["contact"],
            "email": data["email"],
            "password": hashed_password,
            "address": data["address"],
            "last_donation_date": data.get("last_donation_date"),
            "eligible_next_donation": data["eligible_next_donation"],
            "health_conditions": data.get("health_conditions", "None"),
            "preferred_location": data["preferred_location"],
            "donor_status": data["donor_status"],
            "registered_at": datetime.datetime.utcnow()  # Timestamp
        }

        donors_collection.insert_one(donor)

        return jsonify({"message": "Registration Successful!"}), 201

    except Exception as e:
        print(f"Error registering donor: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Login API
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        donor = donors_collection.find_one({"email": data.get("email")})

        if donor and bcrypt.check_password_hash(donor["password"], data.get("password")):
            token = jwt.encode(
                {"email": donor["email"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=3)},
                app.config['SECRET_KEY'],
                algorithm="HS256"
            )
            return jsonify({"message": "Login successful!", "token": token}), 200

        return jsonify({"message": "Invalid email or password"}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get Donors API
@app.route('/donors', methods=['GET'])
def get_donors():
    try:
        donors = list(donors_collection.find({}, {"_id": 0, "password": 0}))
        return jsonify(donors), 200
    except Exception as e:
        print(f"Error fetching donors: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Manage Camps API
@app.route('/camps', methods=['GET', 'POST'])
def manage_camps():
    try:
        if request.method == 'GET':
            camps = list(camps_collection.find({}, {"_id": 0}))
            return jsonify(camps), 200

        elif request.method == 'POST':
            data = request.json
            required_fields = ["name", "location", "date", "available_spots"]

            if not all(key in data for key in required_fields):
                return jsonify({"message": "Missing required fields"}), 400

            data["created_at"] = datetime.datetime.utcnow()  # Add timestamp
            camps_collection.insert_one(data)

            return jsonify({"message": "Camp added successfully!"}), 201

    except Exception as e:
        print(f"Error managing camps: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Home Route
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to Blood Donation API"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=45171, host="0.0.0.0")
