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

class Assignment:
    def __init__(self, course, assignment, is_missing, is_submitted, is_late, is_graded, points, due_date):
        self.course = course
        self.assignment = assignment
        self.is_missing = is_missing
        self.is_submitted = is_submitted
        self.is_late = is_late
        self.is_graded = is_graded
        self.points = points
        self.due_date = due_date
        
    def get_points(self):
        return " 0" if self.points is None else "%2d" % int(self.points)
    
    def get_days_ago(self):
        due_date = datetime.strptime(self.due_date, format_string)
        return due_date - datetime.now()
        
    def get_due_date(self):
        due_in = self.get_days_ago()
        return f"due {-due_in.days} days ago" if due_in.days < 0 else f"due in {due_in.days} days"

def get_assignments(class_name = None):
    start_date = "2025-08-25T00:00:00.000Z"
    end_date = (datetime.today() + timedelta(days=7)).strftime('%Y-%m-%dT00:00:00.000Z')
    url = f"{base_url}/api/v1/planner/items?start_date={start_date}&end_date={end_date}&include%5B%5D=account_calendars&include%5B%5D=all_courses&observed_user_id={user_id}&order=desc&per_page=1000"
    response = requests.get(url, headers={"Authorization":f"Bearer {auth_token}"})

    if response.status_code != 200:
        print(f"Response Failed - {response}")
        return []

    data = response.json()

    with open("data/response.json", 'w') as f:
        f.write(response.text)

    assignments = []
    for item in data:
        try:
            record_type = item['plannable_type']
            if record_type == "assignment":
                course = item['context_name']
                if course in classes:
                    course = classes[course].ljust(12)
                is_missing = item['submissions']['missing']
                is_submitted = item['submissions']['submitted']
                is_late = item['submissions']['late']
                # excused = item['submissions']['excused']
                is_graded = item['submissions']['graded']
                # needs_grading = item['submissions']['needs_grading']
                # has_feedback = item['submissions']['has_feedback']
                # redo_request = item['submissions']['redo_request']
                points = item['plannable']['points_possible']
                assignment = item['plannable']['title']
                due_date = item['plannable']['due_at']
                assn = Assignment(course, assignment, is_missing, is_submitted, is_late, is_graded, points, due_date)
                if class_name is None or class_name == assn.course:
                    # print(item)
                    # print("")
                    assignments.append(assn)
        except Exception as e:
            print("Got an exception processing record. Node appears below")
            print(item)
    return assignments

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
        print(f"Class grades for {course}")
        print("submitted  graded  missing  late  points  due date  assignment")
        for a in assignments:
            if a.course.strip() != course:
                continue
            if (not submitted and a.is_submitted) or (not graded and a.is_graded) or (not missing and a.is_missing) or (not late and a.is_late):
                continue
            print(f"    {good(a.is_submitted).ljust(6)}  {good(a.is_graded).ljust(6)} {bad(a.is_missing).ljust(6)} {bad(a.is_late)}     {num(a.points, 3)}   {date(a.due_date)}  {a.assignment}")  
        print("")

def good(value):
    return "✅" if value else "⚪" # ✅❌
def bad(value):
    return "❌" if value else "⚪" # ✅❌
def str(value, length):
    return value[:length] if len(value)>length else value.ljust(length)
def date(value):
    return value[2:10]
def num(value, length):
    if value is None:
        return " " * length
    return f"{int(value)}".ljust(length)

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
