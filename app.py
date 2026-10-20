import os
import sqlite3
from datetime import date
from flask import Flask, flash, redirect, render_template, request, url_for
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-for-real-deployment")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "attendance.db"))

metrics = PrometheusMetrics(app, group_by="endpoint")
metrics.info("attendance_app_info", "Student Attendance System", version="1.0.0")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            course TEXT NOT NULL DEFAULT ''
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
            UNIQUE(student_id, attendance_date),
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
        )""")


@app.route("/")
def index():
    with get_db() as db:
        students = db.execute("""
            SELECT s.id, s.roll_number, s.name, s.course,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_days,
                   COUNT(a.id) AS marked_days
            FROM students s LEFT JOIN attendance a ON a.student_id = s.id
            GROUP BY s.id ORDER BY s.roll_number
        """).fetchall()
    rows = []
    for student in students:
        row = dict(student)
        row["percentage"] = round((row["present_days"] / row["marked_days"] * 100), 1) if row["marked_days"] else 0
        rows.append(row)
    return render_template("index.html", students=rows, today=date.today().isoformat())


@app.route("/students/add", methods=["POST"])
def add_student():
    roll_number = request.form.get("roll_number", "").strip()
    name = request.form.get("name", "").strip()
    course = request.form.get("course", "").strip()
    if not roll_number or not name:
        flash("Roll number and student name are required.", "error")
        return redirect(url_for("index"))
    try:
        with get_db() as db:
            db.execute("INSERT INTO students (roll_number, name, course) VALUES (?, ?, ?)", (roll_number, name, course))
        flash("Student added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("That roll number already exists.", "error")
    return redirect(url_for("index"))


@app.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    with get_db() as db:
        db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    flash("Student deleted.", "success")
    return redirect(url_for("index"))


@app.route("/attendance", methods=["POST"])
def mark_attendance():
    attendance_date = request.form.get("attendance_date", date.today().isoformat())
    try:
        date.fromisoformat(attendance_date)
    except ValueError:
        flash("Please select a valid date.", "error")
        return redirect(url_for("index"))
    with get_db() as db:
        students = db.execute("SELECT id FROM students").fetchall()
        for student in students:
            status = request.form.get(f"status_{student['id']}")
            if status in ("Present", "Absent"):
                db.execute("""INSERT INTO attendance (student_id, attendance_date, status)
                    VALUES (?, ?, ?) ON CONFLICT(student_id, attendance_date)
                    DO UPDATE SET status = excluded.status""", (student["id"], attendance_date, status))
    flash(f"Attendance saved for {attendance_date}.", "success")
    return redirect(url_for("history", attendance_date=attendance_date))


@app.route("/history")
def history():
    attendance_date = request.args.get("attendance_date", date.today().isoformat())
    with get_db() as db:
        records = db.execute("""
            SELECT s.roll_number, s.name, s.course, a.status, a.attendance_date
            FROM attendance a JOIN students s ON s.id = a.student_id
            WHERE a.attendance_date = ? ORDER BY s.roll_number
        """, (attendance_date,)).fetchall()
    return render_template("history.html", records=records, attendance_date=attendance_date)


@app.get("/health")
def health():
    return {"status": "ok", "service": "student-attendance"}, 200


@app.get("/ready")
def ready():
    try:
        with get_db() as db:
            db.execute("SELECT 1").fetchone()
        return {"status": "ready"}, 200
    except sqlite3.Error:
        return {"status": "not ready"}, 503


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
