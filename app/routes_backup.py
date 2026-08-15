@main.route("/admin/leaves/<int:id>/update", methods=["POST"])
@role_required("admin")
def update_leave(id):
    l = db.session.get(LeaveRequest, id)

    if not l:
        flash("Leave request not found.", "danger")
        return redirect(url_for("main.admin_leaves"))

    # Get requested action
    action = request.form.get("status", "").lower()

    if action not in ["approved", "rejected"]:
        flash("Invalid leave action.", "danger")
        return redirect(url_for("main.admin_leaves"))

    l.status = action

    # ---------------------------------------------------------
    # REJECTED LEAVE
    # ---------------------------------------------------------
    if action == "rejected":

        notify(
            l.faculty.user_id,
            "Leave Rejected",
            f"Your {l.leave_type} leave for "
            f"{l.leave_date} was rejected."
        )

        db.session.commit()

        flash("Leave rejected.", "warning")
        return redirect(url_for("main.admin_leaves"))

    # ---------------------------------------------------------
    # APPROVED LEAVE
    # ---------------------------------------------------------

    attendance_status = (
        "emergency_leave"
        if l.leave_type == "emergency"
        else "leave"
    )

    # Mark faculty attendance
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

    # Notify faculty that leave was approved
    notify(
        l.faculty.user_id,
        "Leave Approved",
        f"Your {l.leave_type} leave for "
        f"{l.leave_date} has been approved."
    )

    # ---------------------------------------------------------
    # FIND THE DAY NAME
    # ---------------------------------------------------------

    day_name = l.leave_date.strftime("%A")

    # Find all timetable classes for this faculty
    affected_classes = Timetable.query.filter_by(
        faculty_id=l.faculty_id,
        day=day_name
    ).all()

    substitutions_created = 0

    # ---------------------------------------------------------
    # CREATE SUBSTITUTIONS
    # ---------------------------------------------------------

    for timetable in affected_classes:

        # Prevent duplicate substitution
        existing = Substitution.query.filter_by(
            timetable_id=timetable.id,
            substitution_date=l.leave_date
        ).first()

        if existing:
            continue

        # Ask AI engine for replacement candidates
        candidates = ai_engine.recommend_substitutes(
            timetable.faculty,
            timetable,
            FacultyProfile.query.all()
        )

        if not candidates:
            notify(
                l.faculty.user_id,
                "Replacement Faculty Not Found",
                f"No available replacement was found for "
                f"{timetable.subject.name} at "
                f"{timetable.start_time.strftime('%H:%M')}."
            )
            continue

        # Best AI candidate
        best = candidates[0]
        replacement = best["faculty"]

        # Create substitution
        substitution = Substitution(
            timetable_id=timetable.id,
            substitution_date=l.leave_date,
            absent_faculty_id=l.faculty_id,
            replacement_faculty_id=replacement.id,
            reason="Approved faculty leave - AI recommendation",
            ai_score=best.get("score", 0),
            status="recommended"
        )

        db.session.add(substitution)

        substitutions_created += 1

        # -----------------------------------------------------
        # NOTIFY REPLACEMENT FACULTY
        # -----------------------------------------------------

        notify(
            replacement.user_id,
            "Substitution Required",
            f"You have been recommended to handle "
            f"{timetable.subject.name} for "
            f"{timetable.class_room.name} on "
            f"{l.leave_date.strftime('%d-%m-%Y')} at "
            f"{timetable.start_time.strftime('%H:%M')}."
        )

        # -----------------------------------------------------
        # NOTIFY STUDENTS
        # -----------------------------------------------------

        students = StudentProfile.query.filter_by(
            class_id=timetable.class_id
        ).all()

        for student in students:

            notify(
                student.user_id,
                "Faculty Change",
                f"{timetable.subject.name} on "
                f"{l.leave_date.strftime('%d-%m-%Y')} at "
                f"{timetable.start_time.strftime('%H:%M')} "
                f"will be handled by "
                f"{replacement.user.name} "
                f"(substitute)."
            )

    db.session.commit()

    # ---------------------------------------------------------
    # ADMIN NOTIFICATION / MESSAGE
    # ---------------------------------------------------------

    flash(
        f"Leave approved. {substitutions_created} "
        f"substitution(s) created.",
        "success"
    )

    return redirect(url_for("main.admin_leaves"))