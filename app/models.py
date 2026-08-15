from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# =========================================================
# FACULTY - SUBJECT ASSOCIATION
# =========================================================

faculty_subjects = db.Table(
    "faculty_subjects",
    db.Column(
        "faculty_id",
        db.Integer,
        db.ForeignKey("faculty_profile.id"),
        primary_key=True
    ),
    db.Column(
        "subject_id",
        db.Integer,
        db.ForeignKey("subject.id"),
        primary_key=True
    )
)


# =========================================================
# USER
# =========================================================

class User(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(30),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =========================================================
# DEPARTMENT
# =========================================================

class Department(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    subjects = db.relationship(
        "Subject",
        foreign_keys="Subject.department_id",
        lazy=True
    )
# =========================================================
# CLASS ROOM
# =========================================================

class ClassRoom(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    year = db.Column(
        db.Integer,
        nullable=False
    )

    section = db.Column(
        db.String(10),
        nullable=False
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("department.id"),
        nullable=False
    )

    department = db.relationship(
        "Department"
    )


# =========================================================
# SUBJECT
# =========================================================

class Subject(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    code = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("department.id"),
        nullable=False
    )

    department = db.relationship(
        "Department"
    )


# =========================================================
# FACULTY PROFILE
# =========================================================

class FacultyProfile(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        unique=True,
        nullable=False
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("department.id"),
        nullable=False
    )

    employee_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    designation = db.Column(
        db.String(100)
    )

    monthly_salary = db.Column(
        db.Float,
        default=0
    )

    user = db.relationship(
        "User"
    )

    department = db.relationship(
        "Department"
    )

    subjects = db.relationship(
        "Subject",
        secondary=faculty_subjects,
        backref="faculty_members"
    )


# =========================================================
# STUDENT PROFILE
# =========================================================

class StudentProfile(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        unique=True,
        nullable=False
    )

    roll_number = db.Column(
        db.String(40),
        unique=True,
        nullable=False
    )

    class_id = db.Column(
        db.Integer,
        db.ForeignKey("class_room.id"),
        nullable=False
    )

    user = db.relationship(
        "User"
    )

    class_room = db.relationship(
        "ClassRoom"
    )


# =========================================================
# TIMETABLE
# =========================================================

class Timetable(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    day = db.Column(
        db.String(15),
        nullable=False
    )

    start_time = db.Column(
        db.Time,
        nullable=False
    )

    end_time = db.Column(
        db.Time,
        nullable=False
    )

    room = db.Column(
        db.String(50),
        nullable=False
    )

    class_id = db.Column(
        db.Integer,
        db.ForeignKey("class_room.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id"),
        nullable=False
    )

    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculty_profile.id"),
        nullable=False
    )

    class_room = db.relationship(
        "ClassRoom"
    )

    subject = db.relationship(
        "Subject"
    )

    faculty = db.relationship(
        "FacultyProfile"
    )


# =========================================================
# FACULTY ATTENDANCE
# =========================================================

class Attendance(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculty_profile.id"),
        nullable=False
    )

    attendance_date = db.Column(
        db.Date,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False
    )

    marked_at = db.Column(
        db.DateTime
    )

    faculty = db.relationship(
        "FacultyProfile"
    )


# =========================================================
# FACULTY LEAVE REQUEST
# =========================================================

class LeaveRequest(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculty_profile.id"),
        nullable=False
    )

    leave_date = db.Column(
        db.Date,
        nullable=False
    )

    leave_type = db.Column(
        db.String(30),
        nullable=False
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    faculty = db.relationship(
        "FacultyProfile"
    )


# =========================================================
# SALARY RECORD
# =========================================================

class SalaryRecord(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculty_profile.id"),
        nullable=False
    )

    month = db.Column(
        db.String(20),
        nullable=False
    )

    basic_salary = db.Column(
        db.Float,
        nullable=False
    )

    allowances = db.Column(
        db.Float,
        default=0
    )

    deductions = db.Column(
        db.Float,
        default=0
    )

    net_salary = db.Column(
        db.Float,
        nullable=False
    )

    faculty = db.relationship(
        "FacultyProfile"
    )


# =========================================================
# SUBSTITUTION
# =========================================================

class Substitution(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    timetable_id = db.Column(
        db.Integer,
        db.ForeignKey("timetable.id"),
        nullable=False
    )

    substitution_date = db.Column(
        db.Date,
        nullable=True
    )

    absent_faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculty_profile.id"),
        nullable=False
    )

    replacement_faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculty_profile.id"),
        nullable=False
    )

    reason = db.Column(
        db.String(255),
        nullable=False
    )

    ai_score = db.Column(
        db.Float,
        default=0
    )

    status = db.Column(
        db.String(30),
        default="recommended"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    timetable = db.relationship(
        "Timetable"
    )

    absent_faculty = db.relationship(
        "FacultyProfile",
        foreign_keys=[absent_faculty_id]
    )

    replacement_faculty = db.relationship(
        "FacultyProfile",
        foreign_keys=[replacement_faculty_id]
    )


# =========================================================
# NOTIFICATION
# =========================================================

class Notification(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    title = db.Column(
        db.String(160),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User"
    )


# =========================================================
# STUDENT ATTENDANCE
# =========================================================

class StudentAttendance(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student_profile.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id"),
        nullable=False
    )

    attendance_date = db.Column(
        db.Date,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False
    )

    student = db.relationship(
        "StudentProfile"
    )

    subject = db.relationship(
        "Subject"
    )


# =========================================================
# STUDENT PERFORMANCE
# =========================================================

class StudentPerformance(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student_profile.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id"),
        nullable=False
    )

    exam_name = db.Column(
        db.String(100),
        nullable=False
    )

    marks = db.Column(
        db.Float,
        nullable=False
    )

    max_marks = db.Column(
        db.Float,
        nullable=False,
        default=100
    )

    grade = db.Column(
        db.String(5)
    )

    student = db.relationship(
        "StudentProfile"
    )

    subject = db.relationship(
        "Subject"
    )
    # =========================================================
# STUDY NOTES
# =========================================================

class StudyNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculty_profile.id"),
        nullable=False
    )

    class_id = db.Column(
        db.Integer,
        db.ForeignKey("class_room.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    faculty = db.relationship("FacultyProfile")
    class_room = db.relationship("ClassRoom")
    subject = db.relationship("Subject")


# =========================================================
# ASSIGNMENTS
# =========================================================

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculty_profile.id"),
        nullable=False
    )

    class_id = db.Column(
        db.Integer,
        db.ForeignKey("class_room.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    due_date = db.Column(
        db.Date,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    faculty = db.relationship("FacultyProfile")
    class_room = db.relationship("ClassRoom")
    subject = db.relationship("Subject")
    # =========================================================
# ASSIGNMENT SUBMISSIONS
# =========================================================

class AssignmentSubmission(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    assignment_id = db.Column(
        db.Integer,
        db.ForeignKey("assignment.id"),
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student_profile.id"),
        nullable=False
    )

    answer = db.Column(
        db.Text,
        nullable=False
    )

    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    marks = db.Column(
        db.Float,
        nullable=True
    )

    feedback = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="submitted"
    )

    assignment = db.relationship(
        "Assignment"
    )

    student = db.relationship(
        "StudentProfile"
    )