from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import URL
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

print("SECRET KEY LOADED:", app.secret_key)

database_url = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME")
)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

def login_required():

    if "user_id" not in session:
        return False

    return True

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    applications = db.relationship("JobApplication", backref="user", lazy=True)

class JobApplication(db.Model):
    __tablename__ = "job_application"
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    application_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    salary = db.Column(db.Float)
    source = db.Column(db.String(100))
    interview_date = db.Column(db.Date)
    notes = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

def get_application_dataframe(user_id):

    applications = JobApplication.query.filter_by(
        user_id=user_id
    ).all()

    data = []

    for application in applications:

        data.append({
            "company": application.company,
            "role": application.role,
            "status": application.status,
            "salary": application.salary,
            "application_date": application.application_date
        })

    df = pd.DataFrame(data)
    df["month"] = pd.to_datetime(
    df["application_date"]
).dt.strftime("%Y-%m")

    return df   

@app.route("/")
def home():
    return "Job Application System is running!"

@app.route("/add-application", methods=["GET", "POST"])
def add_application():

 if not login_required():
    return redirect(url_for("login"))

 if request.method == "POST":

    company = request.form["company"].strip()
    role = request.form["role"].strip()
    status = request.form["status"].strip()

    if not company or not role or not status:
     return "Company, role and status are required."

    application = JobApplication(
        company=company,
        role=role,
        location=request.form["location"],
        application_date=date.fromisoformat(request.form["application_date"]),
        status=status,
        salary=float(request.form["salary"]) if request.form["salary"] else None,
        source=request.form["source"],
        interview_date=date.fromisoformat(request.form["interview_date"]) if request.form["interview_date"] else None,
        notes=request.form["notes"],
        user_id=session["user_id"]
    )

    db.session.add(application)
    db.session.commit()

    print("Application saved successfully!")
 return render_template("add_application.html")


@app.route("/applications")
def applications():

    if not login_required():
        return redirect(url_for("login"))

    search = request.args.get("search", "")
    status = request.args.get("status", "")

    query = JobApplication.query.filter(
        JobApplication.user_id == session["user_id"],
        or_(
            JobApplication.company.ilike(f"%{search}%"),
            JobApplication.role.ilike(f"%{search}%")
        )
    )

    if status:
        query = query.filter(JobApplication.status == status)

    applications = query.all()

    return render_template(
        "applications.html",
        applications=applications,
        search=search,
        status=status
    )
@app.route("/edit-application/<int:id>", methods=["GET", "POST"])
def edit_application(id):

    if not login_required():
        return redirect(url_for("login"))


    application = JobApplication.query.filter_by(
    id=id,
    user_id=session["user_id"]
).first_or_404()

    if request.method == "POST":

        application.company = request.form["company"]
        application.role = request.form["role"]
        application.location = request.form["location"]
        application.application_date = date.fromisoformat(
            request.form["application_date"]
        )
        application.status = request.form["status"]
        application.salary = request.form["salary"]
        application.source = request.form["source"]

        if request.form["interview_date"]:
            application.interview_date = date.fromisoformat(
                request.form["interview_date"]
            )
        else:
            application.interview_date = None

        application.notes = request.form["notes"]

        db.session.commit()

        return redirect(url_for("applications"))

    return render_template(
        "edit_application.html",
        application=application
    )

@app.route("/delete-application/<int:id>", methods=["POST"])
def delete_application(id):

    if not login_required():
        return redirect(url_for("login"))

    application = JobApplication.query.filter_by(
    id=id,
    user_id=session["user_id"]
).first_or_404()

    db.session.delete(application)
    db.session.commit()

    return redirect(url_for("applications"))
with app.app_context():
    db.create_all() 

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
         return "Email already registered. Please use another email."

        user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        print("User registered successfully!")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username

            return redirect(url_for("applications"))

        else:
            print("Invalid email or password")

    return render_template("login.html")


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()

    if not data:
        return {"error": "JSON data required"}, 400

    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        session["user_id"] = user.id
        session["username"] = user.username

        return {
            "message": "Login successful",
            "user_id": user.id
        }

    return {"error": "Invalid email or password"}, 401

@app.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    total = JobApplication.query.filter_by(
        user_id=user_id
    ).count()

    applied = JobApplication.query.filter_by(
        user_id=user_id,
        status="Applied"
    ).count()

    interviews = JobApplication.query.filter_by(
        user_id=user_id,
        status="Interview"
    ).count()

    selected = JobApplication.query.filter_by(
        user_id=user_id,
        status="Selected"
    ).count()

    rejected = JobApplication.query.filter_by(
        user_id=user_id,
        status="Rejected"
    ).count()

    df = get_application_dataframe(user_id)

    status_counts = df["status"].value_counts().to_dict()

    monthly_counts = df["month"].value_counts().sort_index().to_dict()
    # print(monthly_counts)
    role_counts = df["role"].value_counts().to_dict()

    company_counts = df["company"].value_counts().to_dict()

    selection_rate = (
    status_counts.get("Selected", 0) / len(df) * 100
    if len(df) > 0
    else 0
)

    average_ctc = (
    df["salary"].dropna().mean()
    if not df["salary"].dropna().empty
    else 0
)


    interview_rate = (
    status_counts.get("Interview", 0) / len(df) * 100
    if len(df) > 0
    else 0
)
    return render_template(
        "dashboard.html",
        username=session["username"],
        total=total,
        applied=applied,
        interviews=interviews,
        selected=selected,
        rejected=rejected,
        status_counts=status_counts,
        selection_rate=selection_rate,
        interview_rate=interview_rate,
        monthly_counts=monthly_counts,
        average_ctc=average_ctc,
        role_counts=role_counts,
        company_counts=company_counts
    )


@app.route("/export-csv")
def export_csv():

    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    df = get_application_dataframe(user_id)

    csv_data = df.to_csv(index=False)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=job_applications.csv"
        }
    )


# @app.route("/api/applications", methods=["GET"])
# def api_applications():

#     if not login_required():
#         return {"error": "Login required"}, 401

@app.route("/api/applications", methods=["GET"])
def api_applications():

    # user_id = 2

    user_id = session["user_id"]

    applications = JobApplication.query.filter_by(
        user_id=user_id
    ).all()

    data = []

    for application in applications:

        data.append({
            "id": application.id,
            "company": application.company,
            "role": application.role,
            "location": application.location,
            "application_date": str(application.application_date),
            "status": application.status,
            "salary": application.salary,
            "source": application.source,
            "interview_date": str(application.interview_date)
                if application.interview_date else None,
            "notes": application.notes
        })

    return {"applications": data}

@app.route("/api/applications", methods=["POST"])
def create_application_api():

    if not login_required():
        return {"error": "Login required"}, 401

    data = request.get_json()

    if not data:
        return {"error": "JSON data required"}, 400

    application = JobApplication(
        company=data["company"],
        role=data["role"],
        location=data.get("location"),
        application_date=date.fromisoformat(data["application_date"]),
        status=data["status"],
        salary=data.get("salary"),
        source=data.get("source"),
        interview_date=(
            date.fromisoformat(data["interview_date"])
            if data.get("interview_date")
            else None
        ),
        notes=data.get("notes"),
        user_id=session["user_id"]
    )

    db.session.add(application)
    db.session.commit()

    return {
        "message": "Application created successfully",
        "id": application.id
    }, 201


@app.route("/api/applications/<int:id>", methods=["PUT"])
def update_application_api(id):

    if not login_required():
        return {"error": "Login required"}, 401

    application = JobApplication.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first()

    if not application:
        return {"error": "Application not found"}, 404

    data = request.get_json()

    if not data:
        return {"error": "JSON data required"}, 400

    if "company" in data:
        application.company = data["company"]

    if "role" in data:
        application.role = data["role"]

    if "location" in data:
        application.location = data["location"]

    if "application_date" in data:
        application.application_date = date.fromisoformat(
            data["application_date"]
        )

    if "status" in data:
        application.status = data["status"]

    if "salary" in data:
        application.salary = data["salary"]

    if "source" in data:
        application.source = data["source"]

    if "interview_date" in data:
        application.interview_date = (
            date.fromisoformat(data["interview_date"])
            if data["interview_date"]
            else None
        )

    if "notes" in data:
        application.notes = data["notes"]

    db.session.commit()

    return {
        "message": "Application updated successfully"
    }

@app.route("/api/applications/<int:id>", methods=["DELETE"])
def delete_application_api(id):

    if not login_required():
        return {"error": "Login required"}, 401



    application = JobApplication.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first()

    if not application:
        return {"error": "Application not found"}, 404

    db.session.delete(application)
    db.session.commit()

    return {
        "message": "Application deleted successfully"
    }


if __name__ == "__main__":
    app.run(debug=True)