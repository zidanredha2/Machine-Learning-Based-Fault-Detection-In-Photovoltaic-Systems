from flask import Flask, render_template, request, redirect, url_for, session, flash
import joblib
import numpy as np
import json
import os
import secrets

app = Flask(__name__)

# Better secret key
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# File to store users
USERS_FILE = "users.json"

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# Load existing users
users = load_users()

# Load trained model
try:
    model = joblib.load("pv_fault_model.pkl")
except:
    print("Warning: Model file not found. Create a dummy model for testing.")
    model = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            flash("Username already exists. Please choose another.")
            return redirect(url_for("register"))
        else:
            users[username] = password
            save_users(users)  # Persist to file
            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["username"] = username
            session.permanent = True  # Make session persistent
            flash(f"Welcome, {username}!")
            return redirect(url_for("prediction"))
        else:
            flash("Invalid username or password. Please try again.")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.")
    return redirect(url_for("login"))

@app.route("/performance")
def performance():
    if "username" not in session:
        flash("Please login to access performance page.")
        return redirect(url_for("login"))
    return render_template("performance.html")

@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    if "username" not in session:
        flash("Please login to access prediction page.")
        return redirect(url_for("login"))

    prediction = None
    if request.method == "POST":
        try:
            V = float(request.form["V"])
            I = float(request.form["I"])
            G = float(request.form["G"])
            P = float(request.form["P"])

            if model is None:
                raise Exception("Model not loaded")

            input_data = np.array([[V, I, G, P]])
            output = model.predict(input_data)[0]

            labels = ["Module Fault", "Generic Fault", "Partial Shading"]
            prediction = {label: "Yes" if val == 1 else "No" for label, val in zip(labels, output)}

            return render_template("result.html", prediction=prediction)

        except Exception as e:
            return render_template("prediction.html", error=str(e))

    return render_template("prediction.html")

@app.route("/result")
def result():
    if "username" not in session:
        flash("Please login to view results.")
        return redirect(url_for("login"))
    return render_template("result.html")

@app.route('/charts')
def chart():
    if "username" not in session:
        flash("Please login to access charts.")
        return redirect(url_for("login"))
    return render_template('chart.html')

if __name__ == "__main__":
    app.run(debug=True)