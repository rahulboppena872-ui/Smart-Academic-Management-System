from datetime import datetime, date
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .models import *
from . import ai_engine


main = Blueprint(
    "main",
    __name__,
    static_folder="static",
    static_url_path="/static"
)


# ---------------------------------------------------------
# AUTH / HELPERS
# ---------------------------------------------------------

def login_required(fn):
    @wraps(fn)
    def w(*a, **k):
        if "user_id" not in session:
            return redirect(url_for("main.login"))
        return fn(*a, **k)

    return w


def role_required(*roles):
    def d(fn):
        @wraps(fn)
        def w(*a, **k):
            if "user_id" not in session:
                return redirect(url_for("main.login"))

            if session.get("role") not in roles:
                flash("Permission denied.", "danger")
                return redirect(url_for("main.dashboard"))

            return fn(*a, **k)

        return w

    return d


def user():
    return db.session.get(User, session.get("user_id"))


def faculty():
    return FacultyProfile.query.filter_by(
        user_id=user().id
    ).first()


def student():
    return StudentProfile.query.filter_by(
        user_id=user().id
    ).first()


def notify(uid, title, msg):
    db.session.add(
        Notification(
            user_id=uid,
            title=title,
            message=msg
        )
    )


def tt_for(fid):
    return Timetable.query.filter_by(
        faculty_id=fid
    ).all()


# Configure AI providers
ai_engine.configure_providers(
    tt_for,
    lambda fid: len(tt_for(fid))
)


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@main.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))

    return render_template("index.html")


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        u = User.query.filter_by(
            email=email
        ).first()

        if u and check_password_hash(
            u.password_hash,
            password
        ):
            session.update(
                user_id=u.id,
                role=u.role,
                name=u.name
            )

            return redirect(
                url_for("main.dashboard")
            )

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template("login.html")

# ---------------------------------------------------------
# SIGN UP
# ---------------------------------------------------------

@main.route("/signup", methods=["GET", "POST"])
def signup():

    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))

    # Load options for signup form
    departments = Department.query.order_by(
        Department.id
    ).all()

    classes = ClassRoom.query.order_by(
        ClassRoom.id
    ).all()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password", ""
        )
        role = request.form.get(
            "role", "student"
        ).strip().lower()

        department_id = request.form.get(
            "department_id",
            type=int
        )

        class_id = request.form.get(
            "class_id",
            type=int
        )

        # Basic validation
        if not name or not email or not password:
            flash(
                "Please fill all required fields.",
                "danger"
            )
            return redirect(url_for("main.signup"))

        if password != confirm_password:
            flash(
                "Passwords do not match.",
                "danger"
            )
            return redirect(url_for("main.signup"))

        if len(password) < 6:
            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )
            return redirect(url_for("main.signup"))

        if role not in ("student", "faculty"):
            flash(
                "Invalid role selected.",
                "danger"
            )
            return redirect(url_for("main.signup"))

        # Check existing email
        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            flash(
                "An account with this email already exists.",
                "danger"
            )
            return redirect(url_for("main.signup"))

        # Faculty validation
        if role == "faculty" and not department_id:
            flash(
                "Please select a department.",
                "danger"
            )
            return redirect(url_for("main.signup"))

        # Student validation
        if role == "student" and not class_id:
            flash(
                "Please select a class.",
                "danger"
            )
            return redirect(url_for("main.signup"))

        try:

            # Create user
            new_user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(
                    password
                ),
                role=role
            )

            db.session.add(new_user)
            db.session.flush()

            # Faculty profile
            if role == "faculty":

                new_profile = FacultyProfile(
                    user_id=new_user.id,
                    department_id=department_id,
                    employee_code=(
                        "FAC"
                        + str(new_user.id).zfill(3)
                    ),
                    designation="Assistant Professor"
                )

                db.session.add(new_profile)

            # Student profile
            elif role == "student":

                new_profile = StudentProfile(
                    user_id=new_user.id,
                    roll_number=(
                        "STU"
                        + str(new_user.id).zfill(3)
                    ),
                    class_id=class_id
                )

                db.session.add(new_profile)

            db.session.commit()

            flash(
                "Account created successfully. Please login.",
                "success"
            )

            return redirect(
                url_for("main.login")
            )

        except Exception as e:

            db.session.rollback()

            flash(
                "Could not create account. Please try again.",
                "danger"
            )

            print("SIGNUP ERROR:", e)

            return redirect(
                url_for("main.signup")
            )

    return render_template(
        "signup.html",
        departments=departments,
        classes=classes
    )
# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@main.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("main.index")
    )


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@main.route("/dashboard")
@login_required
def dashboard():

    u = user()

    # ADMIN
    if u.role == "admin":

        return render_template(
            "admin_dashboard.html",
            user=u,
            faculty_count=FacultyProfile.query.count(),
            student_count=StudentProfile.query.count(),
            pending_leaves=LeaveRequest.query.filter_by(
                status="pending"
            ).count(),
            substitutions=Substitution.query.filter_by(
                status="recommended"
            ).count(),
            departments=Department.query.all(),
            classes=ClassRoom.query.all(),
            faculty=FacultyProfile.query.all()
        )

    # FACULTY
    if u.role == "faculty":

        f = faculty()

        return render_template(
    "faculty_dashboard.html",
    user=u,
    faculty=f,
    timetable=tt_for(f.id),
    leaves=LeaveRequest.query.filter_by(
        faculty_id=f.id
    ).order_by(
        LeaveRequest.created_at.desc()
    ).limit(5).all()
)

    # STUDENT
    s = student()

    student_attendance_records = (
        StudentAttendance.query.filter_by(
            student_id=s.id
        ).order_by(
            StudentAttendance.attendance_date.desc()
        ).all()
    )

    return render_template(
        "student_dashboard.html",
        user=u,
        student=s,
        attendance=student_attendance_records
    )
# ---------------------------------------------------------
# FACULTY ATTENDANCE
# ---------------------------------------------------------

@main.route(
    "/faculty/attendance",
    methods=["GET", "POST"]
)
@role_required("faculty")
def faculty_attendance():

    f = faculty()

    if request.method == "POST":

        db.session.add(
            Attendance(
                faculty_id=f.id,
                attendance_date=date.today(),
                status=request.form["status"],
                marked_at=datetime.now()
            )
        )

        db.session.commit()

        flash(
            "Attendance saved.",
            "success"
        )

        return redirect(
            url_for("main.faculty_attendance")
        )

    records = Attendance.query.filter_by(
        faculty_id=f.id
    ).order_by(
        Attendance.attendance_date.desc()
    ).all()

    return render_template(
        "attendance.html",
        records=records
    )


# ---------------------------------------------------------
# FACULTY LEAVE
# ---------------------------------------------------------

@main.route(
    "/faculty/leave",
    methods=["GET", "POST"]
)
@role_required("faculty")
def faculty_leave():

    f = faculty()

    if request.method == "POST":

        l = LeaveRequest(
            faculty_id=f.id,
            leave_date=datetime.strptime(
                request.form["leave_date"],
                "%Y-%m-%d"
            ).date(),
            leave_type=request.form["leave_type"],
            reason=request.form["reason"]
        )

        db.session.add(l)

        admin = User.query.filter_by(
            role="admin"
        ).first()

        if admin:

            notify(
                admin.id,
                "New leave request",
                f"{f.user.name} submitted "
                f"{l.leave_type} leave for "
                f"{l.leave_date}."
            )

        db.session.commit()

        flash(
            "Leave submitted for approval.",
            "success"
        )

    leaves = LeaveRequest.query.filter_by(
        faculty_id=f.id
    ).order_by(
        LeaveRequest.created_at.desc()
    ).all()

    return render_template(
        "leave.html",
        leaves=leaves
    )


# ---------------------------------------------------------
# ADMIN LEAVES
# ---------------------------------------------------------

@main.route("/admin/leaves")
@role_required("admin")
def admin_leaves():

    return render_template(
        "admin_leaves.html",
        leaves=LeaveRequest.query.order_by(
            LeaveRequest.created_at.desc()
        ).all()
    )


# ---------------------------------------------------------
# APPROVE / REJECT LEAVE
# ---------------------------------------------------------

@main.route(
    "/admin/leave/<int:id>/<action>",
    methods=["POST"]
)
@role_required("admin")
def process_leave(id, action):

    l = db.session.get(
        LeaveRequest,
        id
    )

    if not l or action not in (
        "approve",
        "reject"
    ):
        return redirect(
            url_for("main.admin_leaves")
        )

    # Prevent processing twice
    if l.status != "pending":

        flash(
            "This leave has already been processed.",
            "warning"
        )

        return redirect(
            url_for("main.admin_leaves")
        )

    # -----------------------------------------------------
    # REJECT
    # -----------------------------------------------------

    if action == "reject":

        l.status = "rejected"

        notify(
            l.faculty.user_id,
            "Leave Rejected",
            f"Your {l.leave_type} leave for "
            f"{l.leave_date} was rejected."
        )

        db.session.commit()

        flash(
            "Leave rejected.",
            "warning"
        )

        return redirect(
            url_for("main.admin_leaves")
        )

    # -----------------------------------------------------
    # APPROVE
    # -----------------------------------------------------

    l.status = "approved"

    attendance_status = (
        "emergency_leave"
        if l.leave_type == "emergency"
        else "leave"
    )

    # Update attendance
    attendance = Attendance.query.filter_by(
        faculty_id=l.faculty_id,
        attendance_date=l.leave_date
    ).first()

    if attendance:

        attendance.status = attendance_status
        attendance.marked_at = datetime.utcnow()

    else:

        db.session.add(
            Attendance(
                faculty_id=l.faculty_id,
                attendance_date=l.leave_date,
                status=attendance_status,
                marked_at=datetime.utcnow()
            )
        )

    # Notify absent faculty
    notify(
        l.faculty.user_id,
        "Leave Approved",
        f"Your {l.leave_type} leave for "
        f"{l.leave_date} was approved."
    )

    # -----------------------------------------------------
    # FIND TIMETABLE FOR THAT WEEKDAY
    # -----------------------------------------------------

    day_name = l.leave_date.strftime("%A")

    affected_classes = Timetable.query.filter_by(
        faculty_id=l.faculty_id,
        day=day_name
    ).all()

    substitutions_created = 0

    # -----------------------------------------------------
    # CREATE AI SUBSTITUTIONS
    # -----------------------------------------------------

    for timetable in affected_classes:

        # Prevent duplicate substitution
        existing = Substitution.query.filter_by(
            timetable_id=timetable.id,
            substitution_date=l.leave_date
        ).first()

        if existing:
            continue

        candidates = ai_engine.recommend_substitutes(
            timetable.faculty,
            timetable,
            FacultyProfile.query.all()
        )

        if not candidates:

            notify(
                l.faculty.user_id,
                "Replacement Not Found",
                f"No conflict-free replacement was found "
                f"for {timetable.subject.name} at "
                f"{timetable.start_time.strftime('%H:%M')}."
            )

            continue

        best = candidates[0]

        replacement = best["faculty"]

        substitution = Substitution(
            timetable_id=timetable.id,
            substitution_date=l.leave_date,
            absent_faculty_id=l.faculty_id,
            replacement_faculty_id=replacement.id,
            reason="Approved faculty leave - AI recommendation",
            ai_score=best["score"],
            status="recommended"
        )

        db.session.add(substitution)

        substitutions_created += 1

        # -------------------------------------------------
        # NOTIFY REPLACEMENT FACULTY
        # -------------------------------------------------

        notify(
            replacement.user_id,
            "Substitution Recommendation",
            f"You are recommended to handle "
            f"{timetable.subject.name} for "
            f"{timetable.class_room.name} on "
            f"{l.leave_date.strftime('%d-%m-%Y')} "
            f"at {timetable.start_time.strftime('%H:%M')}."
        )

        # -------------------------------------------------
        # NOTIFY STUDENTS
        # -------------------------------------------------

        students = StudentProfile.query.filter_by(
            class_id=timetable.class_id
        ).all()

        for st in students:

            notify(
                st.user_id,
                "Class Schedule Change",
                f"{timetable.subject.name} on "
                f"{l.leave_date.strftime('%d-%m-%Y')} "
                f"at {timetable.start_time.strftime('%H:%M')} "
                f"will be handled by "
                f"{replacement.user.name}."
            )

    db.session.commit()

    flash(
        f"Leave approved. "
        f"{substitutions_created} substitution(s) created.",
        "success"
    )

    return redirect(
        url_for("main.admin_leaves")
    )


# ---------------------------------------------------------
# ADMIN TIMETABLE
# ---------------------------------------------------------

@main.route("/admin/timetable")
@role_required("admin")
def admin_timetable():

    departments = Department.query.order_by(
        Department.name
    ).all()

    classes = ClassRoom.query.order_by(
        ClassRoom.department_id,
        ClassRoom.year,
        ClassRoom.section
    ).all()

    selected_department = request.args.get(
        "department_id",
        type=int
    )

    selected_class = request.args.get(
        "class_id",
        type=int
    )

    query = Timetable.query

    if selected_class:
        query = query.filter_by(
            class_id=selected_class
        )

    elif selected_department:
        query = query.join(
            ClassRoom
        ).filter(
            ClassRoom.department_id == selected_department
        )

    rows = query.order_by(
        Timetable.day,
        Timetable.start_time
    ).all()

    return render_template(
        "timetable.html",
        rows=rows,
        departments=departments,
        classes=classes,
        selected_department=selected_department,
        selected_class=selected_class
    )


# ---------------------------------------------------------
# SUBSTITUTIONS
# ---------------------------------------------------------

@main.route("/admin/substitutions")
@role_required("admin")
def substitutions():

    return render_template(
        "substitutions.html",
        rows=Substitution.query.order_by(
            Substitution.created_at.desc()
        ).all()
    )


# ---------------------------------------------------------
# AI ANALYZE TIMETABLE
# ---------------------------------------------------------

@main.route(
    "/admin/substitution/analyze/<int:id>",
    methods=["POST"]
)
@role_required("admin")
def analyze(id):

    t = db.session.get(
        Timetable,
        id
    )

    if not t:

        flash(
            "Timetable entry not found.",
            "danger"
        )

        return redirect(
            url_for("main.substitutions")
        )

    candidates = ai_engine.recommend_substitutes(
        t.faculty,
        t,
        FacultyProfile.query.all()
    )

    if not candidates:

        flash(
            "No conflict-free replacement found.",
            "warning"
        )

        return redirect(
            url_for("main.substitutions")
        )

    best = candidates[0]

    s = Substitution(
        timetable_id=t.id,
        absent_faculty_id=t.faculty_id,
        replacement_faculty_id=best["faculty"].id,
        reason="AI recommendation",
        ai_score=best["score"],
        status="recommended"
    )

    db.session.add(s)

    notify(
        best["faculty"].user_id,
        "AI Substitution Recommendation",
        f"Recommended for {t.subject.name} "
        f"in {t.class_room.name} at "
        f"{t.start_time.strftime('%H:%M')}."
    )

    db.session.commit()

    flash(
        f"AI recommended "
        f"{best['faculty'].user.name} "
        f"({best['score']}/100).",
        "success"
    )

    return redirect(
        url_for("main.substitutions")
    )


# ---------------------------------------------------------
# APPROVE SUBSTITUTION
# ---------------------------------------------------------

@main.route(
    "/admin/substitution/<int:id>/approve",
    methods=["POST"]
)
@role_required("admin")
def approve(id):

    s = db.session.get(
        Substitution,
        id
    )

    if not s:

        flash(
            "Substitution not found.",
            "danger"
        )

        return redirect(
            url_for("main.substitutions")
        )

    if s.status == "approved":

        flash(
            "This substitution is already approved.",
            "warning"
        )

        return redirect(
            url_for("main.substitutions")
        )

    timetable = s.timetable

    if not timetable:

        flash(
            "Timetable entry not found.",
            "danger"
        )

        return redirect(
            url_for("main.substitutions")
        )

    s.status = "approved"

    replacement = s.replacement_faculty
    absent = s.absent_faculty

    # Notify replacement faculty
    notify(
        replacement.user_id,
        "Substitution Approved",
        f"You will handle "
        f"{timetable.subject.name} for "
        f"{timetable.class_room.name} "
        f"at {timetable.start_time.strftime('%H:%M')}."
    )

    # Notify absent faculty
    notify(
        absent.user_id,
        "Leave Substitution Confirmed",
        f"Your class {timetable.subject.name} "
        f"at {timetable.start_time.strftime('%H:%M')} "
        f"has been assigned to "
        f"{replacement.user.name}."
    )

    # Notify students
    students = StudentProfile.query.filter_by(
        class_id=timetable.class_id
    ).all()

    for st in students:

        notify(
            st.user_id,
            "Class Schedule Changed",
            f"{timetable.subject.name}: "
            f"{replacement.user.name} "
            f"is the substitute at "
            f"{timetable.start_time.strftime('%H:%M')}."
        )

    db.session.commit()

    flash(
        f"Substitution approved. "
        f"{replacement.user.name} "
        f"is assigned to the class.",
        "success"
    )

    return redirect(
        url_for("main.substitutions")
    )


# ---------------------------------------------------------
# NOTIFICATIONS
# ---------------------------------------------------------

@main.route("/notifications")
@login_required
def notifications():

    return render_template(
        "notifications.html",
        notifications=Notification.query.filter_by(
            user_id=user().id
        ).order_by(
            Notification.created_at.desc()
        ).all()
    )


# =========================================================
# ADMIN OVERVIEW
# =========================================================

@main.route("/admin/overview")
@role_required("admin")
def overview():

    return render_template(
        "admin_overview.html",
        faculty=FacultyProfile.query.all(),
        students=StudentProfile.query.all(),
        salaries=SalaryRecord.query.all(),
        departments=Department.query.all(),
        classes=ClassRoom.query.all()
    )
# =========================================================
# AUTOMATIC TIMETABLE GENERATOR
# =========================================================

def generate_class_timetable(class_obj):

    subjects = Subject.query.filter_by(
        department_id=class_obj.department_id
    ).order_by(
        Subject.id
    ).all()

    if not subjects:
        return 0, []

    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday"
    ]

    slots = [
        ("09:00", "10:00"),
        ("10:00", "11:00"),
        ("11:00", "12:00"),
        ("13:00", "14:00"),
        ("14:00", "15:00")
    ]

    rooms = [
        "101",
        "102",
        "103",
        "201",
        "202",
        "203",
        "301",
        "302",
        "303",
        "304"
    ]

    created = 0
    skipped = []

    for subject in subjects:

        # Find faculty assigned to this subject
        faculty_members = list(
            subject.faculty_members
        )

        if not faculty_members:

            skipped.append(
                f"{subject.code} - {subject.name} "
                f"(no faculty assigned)"
            )

            continue

        scheduled = False

        # Try faculty members one by one
        for faculty_member in faculty_members:

            if scheduled:
                break

            # Try every day
            for day in days:

                if scheduled:
                    break

                # Try every time slot
                for start_text, end_text in slots:

                    if scheduled:
                        break

                    start_time = datetime.strptime(
                        start_text,
                        "%H:%M"
                    ).time()

                    end_time = datetime.strptime(
                        end_text,
                        "%H:%M"
                    ).time()

                    # Check faculty conflict
                    faculty_conflict = Timetable.query.filter(
                        Timetable.faculty_id ==
                        faculty_member.id,

                        Timetable.day ==
                        day,

                        Timetable.start_time ==
                        start_time
                    ).first()

                    if faculty_conflict:
                        continue

                    # Check classroom
                    for room in rooms:

                        room_conflict = Timetable.query.filter(
                            Timetable.room ==
                            room,

                            Timetable.day ==
                            day,

                            Timetable.start_time ==
                            start_time
                        ).first()

                        if room_conflict:
                            continue

                        # Check class conflict
                        class_conflict = Timetable.query.filter(
                            Timetable.class_id ==
                            class_obj.id,

                            Timetable.day ==
                            day,

                            Timetable.start_time ==
                            start_time
                        ).first()

                        if class_conflict:
                            continue

                        # Create timetable entry
                        timetable = Timetable(
                            day=day,
                            start_time=start_time,
                            end_time=end_time,
                            room=room,
                            class_id=class_obj.id,
                            subject_id=subject.id,
                            faculty_id=faculty_member.id
                        )

                        db.session.add(
                            timetable
                        )

                        created += 1
                        scheduled = True

                        break

        if not scheduled:

            skipped.append(
                f"{subject.code} - {subject.name} "
                f"(no free slot/faculty)"
            )

    return created, skipped


# =========================================================
# ADMIN - ADD CLASS
# =========================================================

@main.route("/admin/classes/add", methods=["POST"])
@role_required("admin")
def add_class():

    name = request.form.get(
        "name",
        ""
    ).strip()

    year = request.form.get(
        "year",
        type=int
    )

    section = request.form.get(
        "section",
        ""
    ).strip()

    department_id = request.form.get(
        "department_id",
        type=int
    )

    # =====================================================
    # VALIDATE CLASS DETAILS
    # =====================================================

    if not name or not year or not section or not department_id:

        flash(
            "Please fill all class details.",
            "danger"
        )

        return redirect(
            url_for("main.dashboard")
        )

    # =====================================================
    # CHECK DEPARTMENT
    # =====================================================

    department = Department.query.get(
        department_id
    )

    if not department:

        flash(
            "Invalid department selected.",
            "danger"
        )

        return redirect(
            url_for("main.dashboard")
        )

    # =====================================================
    # CREATE CLASS
    # =====================================================

    new_class = ClassRoom(
        name=name,
        year=year,
        section=section,
        department_id=department_id
    )

    db.session.add(new_class)

    # Get ID before timetable generation
    db.session.flush()

    # =====================================================
    # AUTOMATIC AI TIMETABLE GENERATION
    # =====================================================

    created, skipped = generate_class_timetable(
        new_class
    )

    # =====================================================
    # SAVE CLASS + TIMETABLE
    # =====================================================

    db.session.commit()

    # =====================================================
    # RESULT MESSAGE
    # =====================================================

    if skipped:

        flash(
            f"Class added successfully. "
            f"AI created {created} timetable periods. "
            f"Skipped: {', '.join(skipped)}",
            "warning"
        )

    else:

        flash(
            f"Class added successfully. "
            f"AI automatically created "
            f"{created} timetable periods.",
            "success"
        )

    return redirect(
        url_for("main.dashboard")
    )


# =========================================================
# ADMIN - ASSIGN SUBJECT TO FACULTY
# =========================================================

@main.route("/admin/assign-subject", methods=["POST"])
@role_required("admin")
def assign_subject():

    faculty_id = request.form.get(
        "faculty_id",
        type=int
    )

    subject_id = request.form.get(
        "subject_id",
        type=int
    )

    if not faculty_id or not subject_id:

        flash(
            "Please select faculty and subject.",
            "danger"
        )

        return redirect(
            url_for("main.dashboard")
        )

    selected_faculty = FacultyProfile.query.get(
        faculty_id
    )

    selected_subject = Subject.query.get(
        subject_id
    )

    if not selected_faculty or not selected_subject:

        flash(
            "Invalid faculty or subject.",
            "danger"
        )

        return redirect(
            url_for("main.dashboard")
        )

    if selected_subject in selected_faculty.subjects:

        flash(
            "This subject is already assigned to this faculty.",
            "warning"
        )

        return redirect(
            url_for("main.dashboard")
        )

    selected_faculty.subjects.append(
        selected_subject
    )

    db.session.commit()

    flash(
        f"{selected_subject.name} assigned to "
        f"{selected_faculty.user.name} successfully.",
        "success"
    )

    return redirect(
        url_for("main.dashboard")
    )
# =========================================================
# FACULTY - STUDENT ATTENDANCE
# =========================================================

@main.route("/faculty/student-attendance", methods=["GET", "POST"])
@role_required("faculty")
def student_attendance():

    f = faculty()

    subjects = f.subjects

    timetables = Timetable.query.filter_by(
        faculty_id=f.id
    ).all()

    class_ids = list({
        t.class_id for t in timetables
    })

    classes = (
        ClassRoom.query.filter(
            ClassRoom.id.in_(class_ids)
        ).all()
        if class_ids
        else []
    )

    selected_class_id = request.args.get(
        "class_id",
        type=int
    )

    selected_subject_id = request.args.get(
        "subject_id",
        type=int
    )

    selected_date = request.args.get(
        "attendance_date"
    )

    students = []

    if selected_class_id and selected_subject_id:

        students = StudentProfile.query.filter_by(
            class_id=selected_class_id
        ).order_by(
            StudentProfile.roll_number
        ).all()

    # -----------------------------------------------------
    # SAVE ATTENDANCE
    # -----------------------------------------------------

    if request.method == "POST":

        selected_class_id = request.form.get(
            "class_id",
            type=int
        )

        selected_subject_id = request.form.get(
            "subject_id",
            type=int
        )

        attendance_date_text = request.form.get(
            "attendance_date"
        )

        if not selected_class_id or not selected_subject_id:
            flash(
                "Please select class and subject.",
                "danger"
            )

            return redirect(
                url_for("main.student_attendance")
            )

        if not attendance_date_text:
            flash(
                "Please select attendance date.",
                "danger"
            )

            return redirect(
                url_for("main.student_attendance")
            )

        attendance_date = datetime.strptime(
            attendance_date_text,
            "%Y-%m-%d"
        ).date()

        students = StudentProfile.query.filter_by(
            class_id=selected_class_id
        ).all()

        for st in students:

            status = request.form.get(
                f"status_{st.id}",
                "absent"
            ).lower()

            if status not in ["present", "absent"]:
                status = "absent"

            existing = StudentAttendance.query.filter_by(
                student_id=st.id,
                subject_id=selected_subject_id,
                attendance_date=attendance_date
            ).first()

            if existing:

                existing.status = status

            else:

                db.session.add(
                    StudentAttendance(
                        student_id=st.id,
                        subject_id=selected_subject_id,
                        attendance_date=attendance_date,
                        status=status
                    )
                )

        db.session.commit()

        flash(
            "Student attendance saved successfully.",
            "success"
        )

        return redirect(
            url_for(
                "main.student_attendance",
                class_id=selected_class_id,
                subject_id=selected_subject_id,
                attendance_date=attendance_date_text
            )
        )

    return render_template(
        "student_attendance.html",
        classes=classes,
        subjects=subjects,
        students=students,
        selected_class_id=selected_class_id,
        selected_subject_id=selected_subject_id,
        selected_date=selected_date
    )


# =========================================================
# FACULTY - STUDENT PERFORMANCE
# =========================================================

@main.route("/faculty/student-performance", methods=["GET", "POST"])
@role_required("faculty")
def student_performance():

    f = faculty()

    subjects = f.subjects

    timetables = Timetable.query.filter_by(
        faculty_id=f.id
    ).all()

    class_ids = list({
        t.class_id for t in timetables
    })

    classes = (
        ClassRoom.query.filter(
            ClassRoom.id.in_(class_ids)
        ).all()
        if class_ids
        else []
    )

    selected_class_id = request.args.get(
        "class_id",
        type=int
    )

    selected_subject_id = request.args.get(
        "subject_id",
        type=int
    )

    selected_exam = request.args.get(
        "exam_name",
        ""
    )

    students = []

    if selected_class_id:

        students = StudentProfile.query.filter_by(
            class_id=selected_class_id
        ).order_by(
            StudentProfile.roll_number
        ).all()

    # -----------------------------------------------------
    # SAVE PERFORMANCE
    # -----------------------------------------------------

    if request.method == "POST":

        selected_class_id = request.form.get(
            "class_id",
            type=int
        )

        selected_subject_id = request.form.get(
            "subject_id",
            type=int
        )

        exam_name = request.form.get(
            "exam_name",
            "Internal"
        ).strip()

        max_marks_text = request.form.get(
            "max_marks",
            "100"
        )

        if not selected_class_id or not selected_subject_id:
            flash(
                "Please select class and subject.",
                "danger"
            )

            return redirect(
                url_for("main.student_performance")
            )

        if not exam_name:
            flash(
                "Please enter exam name.",
                "danger"
            )

            return redirect(
                url_for("main.student_performance")
            )

        try:
            max_marks = float(max_marks_text)

            if max_marks <= 0:
                raise ValueError

        except ValueError:

            flash(
                "Maximum marks must be greater than zero.",
                "danger"
            )

            return redirect(
                url_for("main.student_performance")
            )

        students = StudentProfile.query.filter_by(
            class_id=selected_class_id
        ).all()

        for st in students:

            marks_text = request.form.get(
                f"marks_{st.id}"
            )

            if marks_text is None or marks_text.strip() == "":
                continue

            try:
                marks = float(marks_text)

            except ValueError:
                continue

            marks = max(
                0,
                min(marks, max_marks)
            )

            percentage = (
                marks / max_marks
            ) * 100

            if percentage >= 90:
                grade = "A+"

            elif percentage >= 80:
                grade = "A"

            elif percentage >= 70:
                grade = "B+"

            elif percentage >= 60:
                grade = "B"

            elif percentage >= 50:
                grade = "C"

            elif percentage >= 40:
                grade = "D"

            else:
                grade = "F"

            existing = StudentPerformance.query.filter_by(
                student_id=st.id,
                subject_id=selected_subject_id,
                exam_name=exam_name
            ).first()

            if existing:

                existing.marks = marks
                existing.max_marks = max_marks
                existing.grade = grade

            else:

                db.session.add(
                    StudentPerformance(
                        student_id=st.id,
                        subject_id=selected_subject_id,
                        exam_name=exam_name,
                        marks=marks,
                        max_marks=max_marks,
                        grade=grade
                    )
                )

        db.session.commit()

        flash(
            "Student performance saved successfully.",
            "success"
        )

        return redirect(
            url_for(
                "main.student_performance",
                class_id=selected_class_id,
                subject_id=selected_subject_id,
                exam_name=exam_name
            )
        )

    return render_template(
        "student_performance.html",
        classes=classes,
        subjects=subjects,
        students=students,
        selected_class_id=selected_class_id,
        selected_subject_id=selected_subject_id,
        selected_exam=selected_exam
    )
# ---------------------------------------------------------
# FACULTY - NOTES
# ---------------------------------------------------------

@main.route("/faculty/notes", methods=["GET", "POST"])
@role_required("faculty")
def faculty_notes():
    f = faculty()

    subjects = f.subjects

    timetables = Timetable.query.filter_by(
        faculty_id=f.id
    ).all()

    class_ids = list({t.class_id for t in timetables})

    classes = (
        ClassRoom.query.filter(
            ClassRoom.id.in_(class_ids)
        ).all()
        if class_ids
        else []
    )

    if request.method == "POST":
        class_id = request.form.get("class_id", type=int)
        subject_id = request.form.get("subject_id", type=int)
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if not class_id or not subject_id:
            flash("Please select class and subject.", "danger")
            return redirect(url_for("main.faculty_notes"))

        if not title or not content:
            flash("Title and content are required.", "danger")
            return redirect(url_for("main.faculty_notes"))

        note = StudyNote(
            title=title,
            content=content,
            subject_id=subject_id,
            faculty_id=f.id,
            class_id=class_id
        )

        db.session.add(note)
        db.session.commit()

        flash("Study note added successfully.", "success")
        return redirect(url_for("main.faculty_notes"))

    notes = (
        StudyNote.query
        .filter_by(faculty_id=f.id)
        .order_by(StudyNote.created_at.desc())
        .all()
    )

    return render_template(
        "faculty_notes.html",
        faculty=f,
        subjects=subjects,
        classes=classes,
        notes=notes
    )
# ---------------------------------------------------------
# FACULTY - ATTENDANCE REPORT
# ---------------------------------------------------------

@main.route("/faculty/attendance-report")
@role_required("faculty")
def attendance_report():
    f = faculty()

    classes = ClassRoom.query.all()
    subjects = f.subjects

    selected_class_id = request.args.get(
        "class_id",
        type=int
    )

    selected_subject_id = request.args.get(
        "subject_id",
        type=int
    )

    report = []

    students = []

    if selected_class_id:
        students = StudentProfile.query.filter_by(
            class_id=selected_class_id
        ).all()

    for st in students:

        query = StudentAttendance.query.filter_by(
            student_id=st.id
        )

        if selected_subject_id:
            query = query.filter_by(
                subject_id=selected_subject_id
            )

        records = query.all()

        present = sum(
            1 for r in records
            if str(r.status).lower() == "present"
        )

        absent = sum(

            1 for r in records
            if str(r.status).lower() == "absent"
        )

        total = present + absent

        percentage = (
            round((present / total) * 100, 2)
            if total
            else 0
        )

        report.append({
            "student": st,
            "present": present,
            "absent": absent,
            "total": total,
            "percentage": percentage
        })

    return render_template(
        "attendance_report.html",
        classes=classes,
        subjects=subjects,
        report=report,
        selected_class_id=selected_class_id,
        selected_subject_id=selected_subject_id
    )
# ---------------------------------------------------------
# FACULTY - ASSIGNMENTS
# ---------------------------------------------------------

@main.route("/faculty/assignments", methods=["GET", "POST"])
@role_required("faculty")
def faculty_assignments():
    f = faculty()

    subjects = f.subjects

    timetables = Timetable.query.filter_by(
        faculty_id=f.id
    ).all()

    class_ids = list({
        t.class_id for t in timetables
    })

    classes = (
        ClassRoom.query.filter(
            ClassRoom.id.in_(class_ids)
        ).all()
        if class_ids
        else []
    )

    if request.method == "POST":

        class_id = request.form.get(
            "class_id",
            type=int
        )

        subject_id = request.form.get(
            "subject_id",
            type=int
        )

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        due_date = request.form.get(
            "due_date",
            ""
        )

        if not class_id or not subject_id:
            flash(
                "Please select class and subject.",
                "danger"
            )
            return redirect(
                url_for("main.faculty_assignments")
            )

        if not title:
            flash(
                "Assignment title is required.",
                "danger"
            )
            return redirect(
                url_for("main.faculty_assignments")
            )

        assignment = Assignment(
            title=title,
            description=description,
            due_date=due_date,
            faculty_id=f.id,
            subject_id=subject_id,
            class_id=class_id
        )

        db.session.add(assignment)
        db.session.commit()

        flash(
            "Assignment created successfully.",
            "success"
        )

        return redirect(
            url_for("main.faculty_assignments")
        )

    assignments = (
        Assignment.query
        .filter_by(faculty_id=f.id)
        .order_by(Assignment.due_date.desc())
        .all()
    )

    return render_template(
        "faculty_assignments.html",
        faculty=f,
        subjects=subjects,
        classes=classes,
        assignments=assignments
    )
# ---------------------------------------------------------
# FACULTY - ASSIGNMENT SUBMISSIONS
# ---------------------------------------------------------

@main.route("/faculty/assignment-submissions")
@role_required("faculty")
def assignment_submissions():

    f = faculty()

    assignments = (
        Assignment.query
        .filter_by(faculty_id=f.id)
        .order_by(Assignment.due_date.desc())
        .all()
    )

    assignment_ids = [
        a.id for a in assignments
    ]

    submissions = (
        AssignmentSubmission.query
        .filter(
            AssignmentSubmission.assignment_id.in_(assignment_ids)
        )
        .order_by(
            AssignmentSubmission.submitted_at.desc()
        )
        .all()
        if assignment_ids
        else []
    )

    return render_template(
        "assignment_submissions.html",
        faculty=f,
        assignments=assignments,
        submissions=submissions
    )
# ---------------------------------------------------------
# FACULTY - GRADE ASSIGNMENT SUBMISSION
# ---------------------------------------------------------

@main.route(
    "/faculty/assignment-submission/<int:id>/grade",
    methods=["POST"]
)
@role_required("faculty")
def grade_assignment_submission(id):

    f = faculty()

    submission = db.session.get(
        AssignmentSubmission,
        id
    )

    if not submission:
        flash("Submission not found.", "danger")
        return redirect(
            url_for("main.assignment_submissions")
        )

    assignment = submission.assignment

    if not assignment or assignment.faculty_id != f.id:
        flash(
            "You cannot grade this submission.",
            "danger"
        )
        return redirect(
            url_for("main.assignment_submissions")
        )

    marks_text = request.form.get(
        "marks",
        ""
    ).strip()

    feedback = request.form.get(
        "feedback",
        ""
    ).strip()

    try:
        marks = float(marks_text)
    except (TypeError, ValueError):
        flash(
            "Marks must be a valid number.",
            "danger"
        )
        return redirect(
            url_for("main.assignment_submissions")
        )

    if marks < 0 or marks > 100:
        flash(
            "Marks must be between 0 and 100.",
            "danger"
        )
        return redirect(
            url_for("main.assignment_submissions")
        )

    submission.marks = marks
    submission.feedback = feedback
    submission.status = "graded"

    notify(
        submission.student.user_id,
        "Assignment Graded",
        f"Your assignment '{assignment.title}' "
        f"has been graded. Marks: {marks}/100."
    )

    db.session.commit()

    flash(
        "Assignment graded successfully.",
        "success"
    )

    return redirect(
        url_for("main.assignment_submissions")
    )