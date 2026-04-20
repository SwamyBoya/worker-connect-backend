from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ================= DATABASE CONFIG =================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workerconnect.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODELS =================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    availability = db.Column(db.String(50), default="Available")
    skill = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    worker_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    worker_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    comments = db.Column(db.String(300), nullable=False)

# ================= CREATE TABLES =================
with app.app_context():
    db.create_all()

# ================= APIs =================

# REGISTER
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name")
    contact = data.get("contact")
    password = data.get("password")
    role = data.get("role")
    skill = data.get("skill")
    location = data.get("location")

    if not name or not contact or not password or not role:
        return jsonify({"message": "All fields required"}), 400

    existing_user = User.query.filter_by(contact=contact).first()
    if existing_user:
        return jsonify({"message": "User already exists"}), 409

    new_user = User(
        name=name,
        contact=contact,
        password=password,
        role=role,
        skill=skill,
        location=location
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    contact = data.get("contact")
    password = data.get("password")

    user = User.query.filter_by(contact=contact, password=password).first()

    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "name": user.name,
        "role": user.role,
        "id": user.id
    })


# GET WORKERS
@app.route("/workers", methods=["GET"])
def get_workers():
    name = request.args.get("name")
    availability = request.args.get("availability")
    skill = request.args.get("skill")

    query = User.query.filter_by(role="worker")

    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    if availability:
        query = query.filter_by(availability=availability)
    if skill:
        query = query.filter(User.skill.ilike(f"%{skill}%"))

    workers = query.all()

    result = []
    for w in workers:
        feedbacks = Feedback.query.filter_by(worker_name=w.name).all()

        avg_rating = 0.0
        if feedbacks:
            avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks)

        result.append({
            "id": w.id,
            "name": w.name,
            "contact": w.contact,
            "availability": w.availability,
            "skill": w.skill if w.skill else "Not specified",
            "rating": round(avg_rating, 1),
            "rating_count": len(feedbacks)
        })

    return jsonify(result)


# BOOK WORKER
@app.route("/book", methods=["POST"])
def book_worker():
    data = request.get_json()

    new_booking = Booking(
        customer_name=data.get("customer_name"),
        worker_name=data.get("worker_name"),
        date=data.get("date"),
        status="Pending"
    )

    db.session.add(new_booking)
    db.session.commit()

    return jsonify({"message": "Booking successful"})


# WORKER BOOKINGS
@app.route("/worker/bookings/<worker_name>")
def get_worker_bookings(worker_name):
    bookings = Booking.query.filter_by(worker_name=worker_name).all()

    return jsonify([{
        "id": b.id,
        "customer_name": b.customer_name,
        "date": b.date,
        "status": b.status
    } for b in bookings])


# UPDATE BOOKING STATUS
@app.route("/booking/update/<int:id>", methods=["PUT"])
def update_booking(id):
    data = request.get_json()
    booking = Booking.query.get(id)

    if not booking:
        return jsonify({"message": "Not found"}), 404

    booking.status = data.get("status")
    db.session.commit()

    return jsonify({"message": "Updated"})


# CUSTOMER BOOKINGS
@app.route("/customer/bookings/<customer_name>")
def get_customer_bookings(customer_name):
    bookings = Booking.query.filter_by(customer_name=customer_name).all()

    return jsonify([{
        "id": b.id,
        "worker_name": b.worker_name,
        "date": b.date,
        "status": b.status
    } for b in bookings])


# FEEDBACK
@app.route("/feedback", methods=["POST"])
def add_feedback():
    data = request.get_json()

    new_feedback = Feedback(
        customer_name=data["customer_name"],
        worker_name=data["worker_name"],
        rating=float(data["rating"]),
        comments=data["comments"]
    )

    db.session.add(new_feedback)
    db.session.commit()

    return jsonify({"message": "Feedback added"})


# ADMIN PAGES
@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")


@app.route("/admin/users")
def view_users():
    users = User.query.all()
    return render_template("users.html", users=users)


@app.route("/admin/bookings")
def view_bookings():
    bookings = Booking.query.all()
    return render_template("bookings.html", bookings=bookings)


@app.route("/admin/feedback")
def view_feedback():
    feedback = Feedback.query.all()
    return render_template("feedback.html", feedback=feedback)


# HOME
@app.route("/")
def home():
    return "Worker Connect Backend Running"


# RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)