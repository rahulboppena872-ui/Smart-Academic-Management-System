from werkzeug.security import generate_password_hash

from app import create_app
from app.models import db, User, FacultyProfile, Department

app = create_app()

with app.app_context():

    departments = Department.query.order_by(
        Department.id
    ).all()

    created = []
    assigned = []

    for department in departments:

        email = (
            "faculty."
            + department.code.lower()
            + "@college.local"
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if not user:

            user = User(
                name="Prof. " + department.code,
                email=email,
                password_hash=generate_password_hash(
                    "password"
                ),
                role="faculty"
            )

            db.session.add(user)
            db.session.flush()

            faculty = FacultyProfile(
                user_id=user.id,
                department_id=department.id,
                employee_code=(
                    "FAC"
                    + str(user.id).zfill(3)
                ),
                designation="Assistant Professor"
            )

            db.session.add(faculty)

            created.append(department.code)

        else:

            faculty = FacultyProfile.query.filter_by(
                user_id=user.id
            ).first()

        if not faculty:
            print(
                "WARNING: No faculty profile for",
                department.code
            )
            continue

        subject = next(
            iter(department.subjects),
            None
        )

        if not subject:
            print(
                "WARNING: No subjects for",
                department.code
            )
            continue

        if subject not in faculty.subjects:

            faculty.subjects.append(subject)

            assigned.append(
                (
                    department.code,
                    faculty.user.name,
                    subject.code
                )
            )

    db.session.commit()

    print()
    print("======================================")
    print("DEFAULT FACULTY SETUP COMPLETE")
    print("======================================")

    print()
    print("Created:")
    print(created)

    print()
    print("Subjects Assigned:")
    print(assigned)

    print()
    print("All Faculty:")

    for faculty in FacultyProfile.query.all():

        print(
            faculty.id,
            "|",
            faculty.user.name,
            "|",
            faculty.user.email,
            "|",
            faculty.department.code,
            "|",
            [
                subject.code
                for subject in faculty.subjects
            ]
        )
