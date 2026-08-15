_tt_provider=None
_workload_provider=None

def configure_providers(tt_provider, workload_provider):
    global _tt_provider,_workload_provider
    _tt_provider=tt_provider; _workload_provider=workload_provider

def recommend_substitutes(absent_faculty, timetable, faculty_list):
    ranked=[]
    for candidate in faculty_list:
        if candidate.id==absent_faculty.id: continue
        conflicts=[t for t in _tt_provider(candidate.id) if t.day==timetable.day and t.start_time<timetable.end_time and t.end_time>timetable.start_time]
        if conflicts: continue
        subject_match=40 if timetable.subject_id in [s.id for s in candidate.subjects] else 10
        dept_match=20 if candidate.department_id==timetable.subject.department_id else 5
        workload=_workload_provider(candidate.id)
        workload_score=max(0,25-min(workload*5,25))
        score=min(100,subject_match+dept_match+workload_score+15)
        ranked.append({"faculty":candidate,"score":round(score,1)})
    return sorted(ranked,key=lambda x:x["score"],reverse=True)
