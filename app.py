from flask import Flask, render_template, redirect, url_for, session, jsonify, request
from flask_oauthlib.client import OAuth
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = "JasejaPriyansh3000"  # Change this to a random string
load_dotenv()

# Sample data for source and destination cities
cities = ["Mumbai", "Delhi", "Bengaluru", "Pune", "Hyderabad"]

# Generate unique combinations of source and destination cities
bus_combinations = [(src, dest) for src in cities for dest in cities if src != dest]

# Map each combination to a bus
buses = [
    {
        "id": i,
        "route": combination,
        "seats": [{"id": j, "booked": False} for j in range(1, 31)],
    }
    for i, combination in enumerate(bus_combinations, start=1)
]


oauth = OAuth(app)

google = oauth.remote_app(
    "google",
    consumer_key=os.getenv("CONSUMER_KEY"),
    consumer_secret=os.getenv("CONSUMER_SECRET"),
    request_token_params={"scope": "email"},
    base_url="https://www.googleapis.com/oauth2/v1/",
    request_token_url=None,
    access_token_method="POST",
    access_token_url="https://accounts.google.com/o/oauth2/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return google.authorize(callback=url_for("authorized", _external=True))


@app.route("/logout")
def logout():
    session.pop("google_token", None)
    session.pop("user_data", None)
    return redirect(url_for("index"))


@app.route("/login/authorized")
def authorized():
    response = google.authorized_response()

    if response is None or response.get("access_token") is None:
        return "Login failed. Please retry."

    session["google_token"] = (response["access_token"], "")
    user_info = google.get("userinfo")
    print(user_info.data)
    session["user_data"] = {
        "id": user_info.data["id"],
        "email": user_info.data["email"],
        "picture": user_info.data["picture"],
    }

    return redirect(url_for("bus_search"))


@google.tokengetter
def get_google_oauth_token():
    return session.get("google_token")


@app.route("/find_bus", methods=["POST"])
def find_bus():
    if "user_data" not in session:
        return redirect(url_for("index"))

    user_data = session["user_data"]

    source_city = request.form.get("source_city")
    dest_city = request.form.get("dest_city")

    # Find the bus corresponding to the selected route
    selected_bus = next(
        (bus for bus in buses if bus["route"] == (source_city, dest_city)), None
    )

    if not selected_bus:
        return jsonify({"success": False, "message": "Bus not found"}), 404

    return redirect(
        url_for("seat_selection", bus_id=selected_bus["id"], user_data=user_data)
    )


@app.route("/bus_search")
def bus_search():
    if "user_data" not in session:
        return redirect(url_for("index"))

    user_data = session["user_data"]
    return render_template("bus_search.html", user_data=user_data, cities=cities)


@app.route("/bus/<int:bus_id>")
def seat_selection(bus_id):
    selected_bus = next((bus for bus in buses if bus["id"] == bus_id), None)

    if not selected_bus:
        return "Bus not found", 404

    return render_template("seat_selection.html", bus=selected_bus)


@app.route("/book_seat", methods=["POST"])
def book_seat():
    bus_id = int(request.form.get("bus_id"))
    seat_id = int(request.form.get("seat_id"))

    selected_bus = next((bus for bus in buses if bus["id"] == bus_id), None)

    if not selected_bus:
        return jsonify({"success": False, "message": "Bus not found"}), 404

    for seat in selected_bus["seats"]:
        if seat["id"] == seat_id and not seat["booked"]:
            seat["booked"] = True
            return jsonify(
                {"success": True, "message": f"Seat {seat_id} booked successfully"}
            )

    return jsonify(
        {
            "success": False,
            "message": f"Seat {seat_id} is already booked or does not exist",
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
