import os
import requests
from datetime import datetime

auth_token = os.environ['CANVAS_AUTH_TOKEN']
base_url = os.environ['CANVAS_BASE_URL']

format_string = "%Y-%m-%dT%H:%M:%SZ"

class Assignment:
    def __init__(self, course, assignment, is_missing, is_submitted, points, due_date):
        self.course = course
        self.assignment = assignment
        self.is_missing = is_missing
        self.is_submitted = is_submitted
        self.points = points
        self.due_date = due_date
        
    def get_points(self):
        return "XX" if self.points is None else "%2d" % int(self.points)
    
    def get_days_ago(self):
        due_date = datetime.strptime(self.due_date, format_string)
        return due_date - datetime.now()
        
    def get_due_date(self):
        due_in = self.get_days_ago()
        return f"{-due_in.days} days" if due_in.days < 0 else f"{due_in.days} days"



def get_assignments():
    start_date = "2025-08-25T00:00:00.000Z"
    end_date = "2025-09-18T00:00:00.000Z"
    url = f"{base_url}/api/v1/planner/items?start_date={start_date}&end_date={end_date}&include%5B%5D=account_calendars&include%5B%5D=all_courses&observed_user_id=246743&order=desc&per_page=1000"
    response = requests.get(url, headers={"Authorization":f"Bearer {auth_token}"})

    if response.status_code != 200:
        print(f"Response Failed - {response}")
        return []

    data = response.json()

    assignments = []
    for item in data:
        try:
            record_type = item['plannable_type']
            if record_type == "assignment":
                course = item['context_name']
                is_missing = item['submissions']['missing']
                is_submitted = item['submissions']['submitted']
                points = item['plannable']['points_possible']
                assignment = item['plannable']['title']
                due_date = item['plannable']['due_at']
                assn = Assignment(course, assignment, is_missing, is_submitted, points, due_date)
                assignments.append(assn)
        except Exception as e:
            print("Got an exception processing record. Node appears below")
            print(item)
    return assignments

def show_missing(assignments):
    print("The following assignments are MISSING:")
    count = 0
    for a in assignments:
        if a.is_missing and not a.is_submitted:
            count += 1
            print(f" * [{a.get_points()}] due {a.get_due_date()} ago in {a.course} - {a.assignment}")
    print(f"Total Assignments: {count}")
    print("")

def show_pending(assignments):
    print("The following assignments are UPCOMIING:")
    count = 0
    assignments.sort(reverse=True, key=sort_by_due_date)
    for a in assignments:
        if not a.is_missing and not a.is_submitted:
            count += 1
            print(f" * [{a.get_points()}] due in {a.get_due_date()} in {a.course} - {a.assignment}")
    print(f"Total Assignments: {count}")
    print("")

def sort_by_due_date(a):
  return a.get_days_ago()

def show_summary(assignments):
    print(f"Total Assignments: {len(assignments)}")

assignments = get_assignments()
show_missing(assignments)
show_pending(assignments)
show_summary(assignments)

# date_string = "2025-09-17T06:59:59Z"
# format_string = "%Y-%m-%dT%H:%M:%SZ"
# due_date = datetime.strptime(date_string, format_string)

# due_in = due_date - datetime.now()

# print(due_in.days)
