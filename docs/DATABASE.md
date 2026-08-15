# Database

User -> FacultyProfile / StudentProfile
Department -> ClassRoom / Subject
FacultyProfile <-> Subject
ClassRoom + Subject + FacultyProfile -> Timetable
FacultyProfile -> Attendance
FacultyProfile -> LeaveRequest
FacultyProfile -> SalaryRecord
Timetable + absence -> Substitution
User -> Notification
