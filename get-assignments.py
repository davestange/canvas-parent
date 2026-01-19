import json
import re
import os
import requests
from datetime import datetime, timedelta
import argparse  # <-- Add this import

auth_token = os.environ['CANVAS_AUTH_TOKEN']
base_url = os.environ['CANVAS_BASE_URL']
user_id = os.environ['CANVAS_USER_ID']

format_string = "%Y-%m-%dT%H:%M:%SZ"

classes = {
    "Mind and Body Intro 1-P2-Weinberg": "Mind & Body", 
    "English 1-P3-Brunson": "English", 
    "Physics 1 NGSS-P1-Phan Mende": "Physics",
    "Algebra 1-P2-Hervey": "Algebra",
    "U.S. History Ethnic Studies-P4-Stegner": "History",
    "German 1-P1-Wolfstone": "German",
}

IGNORE_LIST = [
    # Example: ("English", "Essay Draft 1"),
    # ("Physics", "0.1 Class Autobiographies"),
    # ("German", "mündliche Prüfung: Kapitel 1, Wer bist du? (UNIT 1 ORAL TEST)"),
    # ("German", "schriftliche Prüfung: Kapitel 1, Wer bist du? (UNIT 1 WRITTEN TEST)"),
    # ("German", "Wer bist du? (German 1-2 survey)"),
]


class Assignment:
    def __init__(self, unique_id, record_type, course, assignment, is_missing, is_submitted, is_late, is_graded, points, due_date, html_url):
        self.unique_id = unique_id
        self.record_type = record_type
        self.course = course
        self.assignment = assignment
        self.is_missing = is_missing
        self.is_submitted = is_submitted
        self.is_late = is_late
        self.is_graded = is_graded
        self.points = points
        self.score = 0
        self.due_date = due_date
        self.html_url = html_url
        
    def get_points(self):
        return " 0" if self.points is None else "%2d" % int(self.points)
    
    def get_days_ago(self):
        due_date = datetime.strptime(self.due_date, format_string)
        return due_date - datetime.now()
        
    def get_due_date(self):
        due_in = self.get_days_ago()
        return f"due {-due_in.days} days ago" if due_in.days < 0 else f"due in {due_in.days} days"

def get_assignments(class_name = None):
    # start_date = "2025-08-27T00:00:00.000Z"
    start_date = "2025-11-01T00:00:00.000Z"
    end_date = (datetime.today() + timedelta(days=7)).strftime('%Y-%m-%dT00:00:00.000Z')
    url = f"{base_url}/api/v1/planner/items?start_date={start_date}&end_date={end_date}&include%5B%5D=account_calendars&include%5B%5D=all_courses&observed_user_id={user_id}&order=desc&per_page=1000"
    response = requests.get(url, headers={"Authorization":f"Bearer {auth_token}"})

    if response.status_code != 200:
        print(f"Response Failed - {response}")
        return []

    data = response.json()

    with open("data/response.json", 'w') as f:
        print(f"")
        f.write(response.text)

    assignments = []
    for item in data:
        try:
            record_type = item['plannable_type']
            if record_type != "assignment":
                continue
            course = item['context_name']
            if course in classes:
                course = classes[course].ljust(12)
            unique_id = f"{item['course_id']}-{item['plannable_id']}"
            is_missing = item['submissions']['missing']
            is_submitted = item['submissions']['submitted']
            is_late = item['submissions']['late']
            is_graded = item['submissions']['graded']
            points = item['plannable']['points_possible']
            assignment = item['plannable']['title']
            due_date = item['plannable']['due_at']
            if not due_date and 'plannable_date' in item:
                due_date = item['plannable_date']
            html_url = item['html_url']
            if due_date is None:
                # filtering out assignments with invalid due date, don't log as them, as there are A LOT
                # print(f"Assignment {assignment} is invalid with due_date=None")
                continue
            assn = Assignment(unique_id, record_type, course, assignment, is_missing, is_submitted, is_late, is_graded, points, due_date, html_url)
            if class_name is None or class_name == assn.course:
                assignments.append(assn)
        except Exception as e:
            print("Got an exception processing record. Node appears below")
            print(item)
    return assignments

def filter_ignore_list(assignments):
    return [a for a in assignments if (a.course.strip(), a.assignment.strip()) not in IGNORE_LIST]

def show_missing(assignments):
    print("The following assignments are MISSING:")
    count = 0
    for a in assignments:
        if a.is_missing:
            count += 1
            
            print(f" 🔴 [{a.get_points()}] {a.get_due_date()} in {a.course} - {a.assignment}")
    print(f"Total Assignments: {count}")
    print("")

def show_pending(assignments):
    print("The following assignments are PENDING:")
    count = 0
    assignments.sort(reverse=True, key=sort_by_due_date)
    for a in assignments:
        if a.get_days_ago().days < 0 and not a.is_missing and not a.is_submitted and not a.is_graded:
            count += 1
            print(f" 🟡 [{a.get_points()}] {a.get_due_date()} in {a.course} - {a.assignment}")
    print(f"Total Assignments: {count}")
    print("")

def show_grades(assignments, submitted=True, graded=True, missing=True, late=True):
    for full_name in classes:
        course = classes[full_name]
        print(f"Class grades for {course} ({full_name})")
        print("submitted  graded  missing  late  score  points  due date  assignment")
        total_points = 0
        total_score = 0
        for a in assignments:
            if a.course.strip() != course:
                continue
            # if (not submitted and a.is_submitted) or (not graded and a.is_graded) or (not missing and a.is_missing) or (not late and a.is_late):
            #     continue
            print(f"    {good(a.is_submitted).ljust(6)}  {good(a.is_graded).ljust(6)} {bad(a.is_missing).ljust(6)} {bad(a.is_late)}  {num(a.score, 5)}  {num(a.points, 5)}   {date(a.due_date)}  {a.assignment}")  
            # if a.is_graded:
            total_points += a.points if a.points is not None else 0
            total_score += a.score if a.score is not None else 0
        grade = 0 if total_points == 0 else 100*total_score/total_points
        print(f"                          total:  {num(total_score, 5)}  {num(total_points, 5)}")
        print(f"                          grade:   {grade:0.2f}")
        print("")

def good(value):
    return "✅" if value else "⚪" # ✅❌
def bad(value):
    return "❌" if value else "⚪" # ✅❌
def str(value, length):
    return value[:length] if len(value)>length else value.ljust(length)
def date(value):
    if not value:
        return "--------"
    return value[2:10]
def num(value, length):
    if value is None:
        return " " * length
    return f"{value:0.1f}".rjust(length)

def show_upcoming(assignments):
    print("The following assignments are UPCOMING:")
    count = 0
    assignments.sort(reverse=True, key=sort_by_due_date)
    for a in assignments:
        if a.get_days_ago().days > 0:
            count += 1
            print(f" 🟢 [{a.get_points()}] {a.get_due_date()} in {a.course} - {a.assignment}")
    print(f"Total Assignments: {count}")
    print("")

def show_all(assignments):
    print("The following assignments are all assignments:")
    count = 0
    assignments.sort(reverse=True, key=sort_by_due_date)
    for a in assignments:
        count += 1
        print(f" * [{a.get_points()}] {a.get_due_date()} in {a.course} - {a.assignment} ({a.due_date})")
        print(f"   is_missing={a.is_missing}, is_submitted={a.is_submitted}, is_late={a.is_late}, is_graded={a.is_graded}")
    print(f"Total Assignments: {count}")
    print("")


def get_grade_from_cache(assn):
    filename = f"course-grades/{assn.unique_id}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            if 'score' in data:
                return data['score']
    else:
        url = f"{base_url}/api/v1{assn.html_url}"
        response = requests.get(url, headers={"Authorization":f"Bearer {auth_token}"})
        if response.status_code == 200:
            data = response.json()
            if 'score' in data:
                with open(filename, "w") as file:
                    file.write(response.text)                
                return data['score']
        else:
            print(f"Failed to fetch grade for {assn.unique_id} from {url}: {response.status_code}") 
    return None


# Fetch and cache grades for assignments
def get_grades(assignments):
    for a in assignments:
        if a.is_graded and a.html_url is not None:
            a.score = get_grade_from_cache(a)
    return assignments

def sort_by_due_date(a):
  return a.get_days_ago()

def show_summary(assignments):
    print(f"Total Assignments: {len(assignments)}")

def main():
    parser = argparse.ArgumentParser(description="Canvas Assignments Viewer")
    parser.add_argument('--view', choices=['original', 'grade'], default='original', help='View type: original or grade')
    args = parser.parse_args()

    filter_by = None
    assignments = get_assignments()
    assignments = filter_ignore_list(assignments)
    assignments = get_grades(assignments)
    if filter_by is not None:
        print(f"💀💀💀 WARNING: Filtering by class={filter_by}\n")
        assignments = [a for a in assignments if a.course.strip() == filter_by]

    if args.view == 'original':
        show_missing(assignments)
        show_pending(assignments)
        show_upcoming(assignments)
    else:
        show_grades(assignments)

if __name__ == "__main__":
    main()
