from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from paypalrestsdk import Payment, configure
from agent_functionalities import update_pot, handle_ollama_attempt
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecretkey")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure PayPal
configure({
    "mode": os.getenv("PAYPAL_MODE", "sandbox"),
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET"),
})

# In-memory data storage
users = {}
user_credits = {}

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"message": "Username and password are required."}), 400
    if username in users:
        return jsonify({"message": "Username already exists."}), 400
    users[username] = generate_password_hash(password)
    user_credits[username] = {"credits": 0, "balance": 0.0}
    logging.info(f"New user registered: {username}")
    return jsonify({"message": "Registration successful!"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"message": "Username and password are required."}), 400
    if username not in users or not check_password_hash(users[username], password):
        return jsonify({"message": "Invalid username or password."}), 401
    session["username"] = username
    logging.info(f"User logged in: {username}")
    return jsonify({"message": "Login successful!", "user": username}), 200


@app.route("/logout", methods=["POST"])
def logout():
    username = session.pop("username", None)
    logging.info(f"User logged out: {username}")
    return jsonify({"message": "Logout successful."}), 200


@app.route("/session", methods=["GET"])
def get_session():
    username = session.get("username")
    if not username:
        return jsonify({"user": None}), 200
    return jsonify({"user": username}), 200


@app.route("/pot", methods=["GET"])
def get_pot():
    try:
        pot_amount = update_pot(0)
        return jsonify({"pot_amount": pot_amount}), 200
    except Exception as e:
        logging.error(f"Error fetching pot amount: {e}")
        return jsonify({"message": "Unable to fetch pot amount."}), 500


@app.route("/credits", methods=["GET"])
def get_credits():
    username = session.get("username")
    if not username:
        return jsonify({"message": "User not logged in."}), 403
    if username not in user_credits:
        return jsonify({"message": "User not found."}), 404
    return jsonify(user_credits[username]), 200


@app.route("/attempt", methods=["POST"])
def process_attempt():
    username = session.get("username")
    if not username:
        return jsonify({"status": "error", "message": "You must log in first."}), 403

    data = request.json
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"status": "error", "message": "Message cannot be empty."}), 400

    if username not in user_credits or user_credits[username]["credits"] <= 0:
        return jsonify({"status": "error", "message": "Not enough credits. Please buy more."}), 403

    logging.info(f"User: {username}, Credits before deduction: {user_credits[username]['credits']}")

    try:
        # Deduct credit and update pot
        user_credits[username]["credits"] -= 1
        attempt_cost = float(os.getenv("ATTEMPT_COST", 1.00))
        pot_amount = update_pot(attempt_cost)

        # Handle LLM response
        agent_response = handle_ollama_attempt(message)
        if agent_response["status"] == "WIN":
            user_credits[username]["balance"] += agent_response["amount"]
            pot_amount = 0.0
        logging.info(f"Attempt processed for user: {username}, Status: {agent_response['status']}")
        return jsonify({
            "status": agent_response["status"],
            "message": agent_response["message"],
            "fun_message": agent_response.get("fun_message"),
            "pot_amount": pot_amount,
        }), 200
    except Exception as e:
        logging.error(f"Error processing attempt for user {username}: {e}")
        return jsonify({"status": "error", "message": "An error occurred.", "error": str(e)}), 500


@app.route("/buy-credits", methods=["POST"])
def buy_credits():
    username = session.get("username")
    if not username:
        return jsonify({"message": "You must log in first."}), 403

    data = request.json
    amount = data.get("amount", 5.00)
    if amount <= 0:
        return jsonify({"message": "Invalid amount specified."}), 400

    payment = Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "transactions": [
            {
                "amount": {"total": f"{amount:.2f}", "currency": "USD"},
                "description": f"Purchase ${amount:.2f} credits",
            }
        ],
        "redirect_urls": {
            "return_url": url_for("execute_payment", _external=True, user=username),
            "cancel_url": url_for("cancel_payment", _external=True),
        },
    })
    if payment.create():
        approval_url = next((link.href for link in payment.links if link.rel == "approval_url"), None)
        if approval_url:
            return jsonify({
                "status": "success",
                "payment_id": payment.id,
                "redirect_url": approval_url,
            }), 200
    logging.error(f"Payment creation failed for user {username}: {payment.error}")
    return jsonify({"status": "error", "message": "Payment creation failed."}), 500


@app.route("/payment/execute", methods=["GET"])
def execute_payment():
    payment_id = request.args.get("paymentId")
    payer_id = request.args.get("PayerID")
    username = session.get("username")
    if not username:
        return jsonify({"message": "You must log in first."}), 403
    if username not in user_credits:
        return jsonify({"message": "User not found."}), 404

    try:
        payment = Payment.find(payment_id)
        if payment.execute({"payer_id": payer_id}):
            user_credits[username]["credits"] += 5
            logging.info(f"Credits added for user {username}: 5 credits.")
            return redirect(url_for("home") + "?message=Credits added successfully.")
        logging.error(f"Payment execution failed for user {username}")
        return jsonify({"message": "Payment execution failed."}), 400
    except Exception as e:
        logging.error(f"Error executing payment for user {username}: {e}")
        return jsonify({"message": "An error occurred while executing payment.", "error": str(e)}), 500


@app.route("/cashout", methods=["POST"])
def cashout():
    username = session.get("username")
    if not username:
        return jsonify({"message": "You must log in first."}), 403

    if username not in user_credits or user_credits[username]["balance"] <= 0:
        return jsonify({"message": "Insufficient balance for cashout."}), 400

    amount = user_credits[username]["balance"]
    user_credits[username]["balance"] = 0.0
    logging.info(f"Cashout request submitted for user {username}: ${amount:.2f}")
    return jsonify({"message": f"Cashout request submitted for ${amount:.2f}. Expect payment soon."}), 200


@app.route("/payment/cancel", methods=["GET"])
def cancel_payment():
    return jsonify({"message": "Payment was cancelled."}), 200


if __name__ == "__main__":
    app.run(host=os.getenv("FLASK_RUN_HOST", "0.0.0.0"), port=int(os.getenv("FLASK_RUN_PORT", 5000)))
