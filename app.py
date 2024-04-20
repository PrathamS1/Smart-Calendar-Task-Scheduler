import os
import json
from datetime import datetime, timedelta
from calendar import monthcalendar, month_name
from flask import Flask, render_template, request

app = Flask(__name__)

def generate_calendar(start_date, end_date, schedule):
    print(start_date, end_date)
    # Generate a calendar grid based on the start and end dates
    calendar = []
    
    # Loop through each month from start_date to end_date
    current_date = start_date
    while current_date.month <= end_date.month:
        # Extract year and month from current_date
        year = current_date.year
        month = current_date.month
        # Generate calendar for the current month
        month_calendar = monthcalendar(year, month)
        print(month_calendar)
        # Initialize list of weeks for current month
        weeks = []
        
        # Iterate over each week in the month's calendar
        for week in month_calendar:
            # Initialize list of days for current week
            days = []
            # Iterate over each day in the week
            for day in week:
                # If day is 0, it's not part of current month, represent it as empty
                if day == 0:
                    days.append({'date': '-', 'tasks': []})
                else:
                    # Format day as two digits string
                    day_str = '{:02d}'.format(day)
                    # Find tasks for current day
                    tasks_on_day = [task for task in schedule if task['date'] == f'{year}-{month:02d}-{day_str}']
                    days.append({'date': day_str, 'tasks': tasks_on_day})
            
            # Add current week to weeks list
            weeks.append(days)
        
        # Add month's data to calendar
        calendar.append({'month': month_name[month], 'year': year, 'weeks': weeks})
        
        # Move to next month
        current_date = current_date.replace(day=1) + timedelta(days=32)
        current_date = current_date.replace(day=1)
        
        # Break loop if the current month exceeds the end_date's month
        if current_date > end_date:
            break
            
    static_folder = os.path.join(os.getcwd(), 'static')
    filename = os.path.join(static_folder, "calendarData.json")
    if filename:
        with open(filename, 'w') as file:
            json.dump(calendar, file, indent=4)
            
    print(calendar)
    return calendar

def round_robin_schedule(tasks, start_date, deadline, max_hours_per_day=8):
    # Implementation of round-robin scheduling using start_date and deadline
    schedule = []
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(deadline, '%Y-%m-%d')
    remaining_hours = 0
    
    while tasks and current_date <= end_date:
        if not remaining_hours:
            # Start a new day
            remaining_hours = max_hours_per_day
        
        task = tasks.pop(0)
        
        if task['hours'] <= remaining_hours:
            # If task can be completed on the same day
            schedule.append({'name': task['name'], 'date': current_date.strftime('%Y-%m-%d'), 'hours': task['hours']})
            remaining_hours -= task['hours']
        else:
            # If task spans multiple days
            schedule.append({'name': task['name'], 'date': current_date.strftime('%Y-%m-%d'), 'hours': remaining_hours})
            task['hours'] -= remaining_hours
            tasks.append(task)
            remaining_hours = 0
        
        current_date += timedelta(days=1)
    
    return schedule

def is_schedule_possible(tasks, start_date, deadline, max_hours_per_day=8):
    # Check if it's possible to schedule all tasks within the timeline
    total_hours_required = sum(task['hours'] for task in tasks)
    total_days_available = (datetime.strptime(deadline, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1
    max_hours_possible = total_days_available * max_hours_per_day
    return total_hours_required <= max_hours_possible

@app.route('/', methods=['GET', 'POST'])
def task_form():
    if request.method == 'POST':
        # Handle form submission
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d')
        max_hours_per_day = int(request.form['work_hours_per_day'])  # Get max hours per day from form
        task_names = request.form.getlist('task_name[]')
        completion_times = request.form.getlist('completion_time[]')
        
        # Convert completion times to integers
        completion_times = [int(time) for time in completion_times]
        tasks = [{'name': name, 'hours': hours} for name, hours in zip(task_names, completion_times)]
        
        # Check if scheduling all tasks is possible within the timeline
        if not is_schedule_possible(tasks, start_date.strftime('%Y-%m-%d'), deadline.strftime('%Y-%m-%d'), max_hours_per_day):
            return render_template('error.html', message="Tasks cannot be scheduled within the given timeline.")
        
        # Perform scheduling
        schedule = round_robin_schedule(tasks, start_date.strftime('%Y-%m-%d'), deadline.strftime('%Y-%m-%d'), max_hours_per_day)
        print(schedule)
        # Generate calendar based on start and deadline dates
        calendar = generate_calendar(start_date, deadline, schedule)
        return render_template('calendar_page.html', calendar=calendar)
    return render_template('task_form.html')

if __name__ == '__main__':
    app.run(debug=True)
