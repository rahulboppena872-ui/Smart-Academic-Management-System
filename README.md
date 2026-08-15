# Smart Academic Management System

AI-assisted school/college management for Admin/Director, Faculty and Students.

## Features
- Role-based login
- Faculty, students, classes and subjects
- Timetable
- Faculty attendance
- Normal and emergency leave
- AI-style substitution recommendations
- Schedule-change notifications
- Faculty salary overview for Admin
- MySQL database

## Stack
Python 3.12+, Flask, SQLAlchemy, MySQL, PyMySQL, HTML/CSS, Bootstrap.

## Run on Windows
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create MySQL database:
```sql
CREATE DATABASE smart_academic_db;
```

Copy `.env.example` to `.env` and set your MySQL password.

Then:
```powershell
python seed.py
python run.py
```

Open http://127.0.0.1:5000

Demo password: `password`
- admin@college.local
- rahul@college.local
- priya@college.local
- anil@college.local
- student@college.local

## Attendance rule
Early attendance does not automatically mean emergency leave. Faculty submit emergency leave and Admin approves it. If there is no attendance and no approved leave after the configured cutoff, the institution can flag unauthorized absence.

## AI substitution
The MVP ranks available faculty using subject match, department match, timetable conflict, workload and availability. It is explainable and can later be replaced by a trained ML model.
