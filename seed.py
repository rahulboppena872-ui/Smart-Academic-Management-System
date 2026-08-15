from werkzeug.security import generate_password_hash
from datetime import time
from app import create_app
from app.models import *
app=create_app()
with app.app_context():
    db.drop_all(); db.create_all()
    cse=Department(name="Computer Science & Engineering",code="CSE"); db.session.add(cse); db.session.flush()
    ca=ClassRoom(name="B.Tech CSE 3-A",year=3,section="A",department_id=cse.id); cb=ClassRoom(name="B.Tech CSE 3-B",year=3,section="B",department_id=cse.id); db.session.add_all([ca,cb]); db.session.flush()
    subs=[Subject(name="Machine Learning",code="ML",department_id=cse.id),Subject(name="Data Analytics",code="DA",department_id=cse.id),Subject(name="Computer Networks",code="CN",department_id=cse.id),Subject(name="Software Engineering",code="SE",department_id=cse.id)]
    db.session.add_all(subs); db.session.flush()
    us=[User(name="System Admin",email="admin@college.local",password_hash=generate_password_hash("password"),role="admin"),
        User(name="Prof. Rahul",email="rahul@college.local",password_hash=generate_password_hash("password"),role="faculty"),
        User(name="Prof. Priya",email="priya@college.local",password_hash=generate_password_hash("password"),role="faculty"),
        User(name="Prof. Anil",email="anil@college.local",password_hash=generate_password_hash("password"),role="faculty"),
        User(name="Aarav Student",email="student@college.local",password_hash=generate_password_hash("password"),role="student")]
    db.session.add_all(us); db.session.flush()
    fs=[FacultyProfile(user_id=us[1].id,department_id=cse.id,employee_code="FAC001",designation="Assistant Professor",monthly_salary=50000,subjects=[subs[0],subs[1]]),
        FacultyProfile(user_id=us[2].id,department_id=cse.id,employee_code="FAC002",designation="Assistant Professor",monthly_salary=52000,subjects=[subs[0],subs[2]]),
        FacultyProfile(user_id=us[3].id,department_id=cse.id,employee_code="FAC003",designation="Associate Professor",monthly_salary=65000,subjects=[subs[2],subs[3]])]
    db.session.add_all(fs); db.session.flush()
    db.session.add(StudentProfile(user_id=us[4].id,roll_number="CSE3A001",class_id=ca.id))
    db.session.add_all([
      Timetable(day="Monday",start_time=time(10),end_time=time(11),room="304",class_id=ca.id,subject_id=subs[0].id,faculty_id=fs[0].id),
      Timetable(day="Monday",start_time=time(11),end_time=time(12),room="205",class_id=ca.id,subject_id=subs[1].id,faculty_id=fs[0].id),
      Timetable(day="Monday",start_time=time(10),end_time=time(11),room="305",class_id=cb.id,subject_id=subs[2].id,faculty_id=fs[1].id),
      Timetable(day="Tuesday",start_time=time(10),end_time=time(11),room="304",class_id=ca.id,subject_id=subs[3].id,faculty_id=fs[2].id)])
    db.session.commit()
    print("Seed complete. Password for all demo users: password")
