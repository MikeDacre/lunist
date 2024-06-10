#!/bin/env python3
# Code is incomplete and non-functional right now
import os
import yaml
import requests
import argparse
from utils import setup_db, Task
from todoist_api_python.api import TodoistAPI

def sync_tasks(config_file='~/.lunist.yaml'):
    # Load configuration
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)

    FILTER = config['filter']['filter_on']
    FILTER_LABEL = config['filter']['filter_label']
    DELETE_ON_COPY = config['filter']['delete_on_copy']

    TODOIST_API_KEY = config['todoist']['api_key']
    LUNATASK_API_KEY = config['lunatask']['api_key']
    PROJECTS_TO_AREAS = config['mapping']['projects_to_areas']
    PRIORITIES = config['mapping']['priorities']
    LABELS_TO_GOALS = config['mapping']['labels_to_goals']
    LABELS_TO_DURATION = config['mapping']['labels_to_duration']

    # Setup the database
    setup_db()

    # Initialize Todoist API
    todoist_api = TodoistAPI(TODOIST_API_KEY)

    # Fetch tasks from Todoist
    tasks = todoist_api.get_tasks(filter='@lunatask')

    # Load existing tasks from the database
    db_tasks = {task.todoist_id: task for task in Task.load_all_tasks()}

    for task in tasks:
        project_name = task.project.name
        if project_name not in PROJECTS_TO_AREAS:
            continue

        area_of_life = PROJECTS_TO_AREAS[project_name]
        priority = PRIORITIES.get(task.priority, 'Low')

        if task.id not in db_tasks:
            # New task
            new_task = Task(
                task_name=task.content,
                task_description=task.description,
                todoist_id=task.id,
                lunatask_id=None,
                todoist_project=project_name,
                lunatask_area=area_of_life,
                priority=priority,
                in_lunatask=False
            )
            new_task.save_to_db()
            db_tasks[task.id] = new_task
        else:
            # Update existing task
            existing_task = db_tasks[task.id]
            existing_task.task_name = task.content
            existing_task.task_description = task.description
            existing_task.priority = priority
            existing_task.save_to_db()

    # Sync with Lunatask
    for task_id, task in db_tasks.items():
        if not task.in_lunatask:
            # Create task in Lunatask
            response = requests.post(
                'https://api.lunatask.com/tasks',
                headers={'Authorization': f'Bearer {LUNATASK_API_KEY}'},
                json={
                    'name': task.task_name,
                    'description': task.task_description,
                    'areaOfLife': task.lunatask_area,
                    'priority': task.priority,
                    'eisenhower': 'urgent' if '@urgent' in task.task_name else 'important' if '@important' in task.task_name else 'none'
                }
            )
            if response.status_code == 201:
                task.lunatask_id = response.json()['id']
                task.in_lunatask = True
                task.save_to_db()
        else:
            # Update task in Lunatask
            response = requests.put(
                f'https://api.lunatask.com/tasks/{task.lunatask_id}',
                headers={'Authorization': f'Bearer {LUNATASK_API_KEY}'},
                json={
                    'name': task.task_name,
                    'description': task.task_description,
                    'areaOfLife': task.lunatask_area,
                    'priority': task.priority,
                    'eisenhower': 'urgent' if '@urgent' in task.task_name else 'important' if '@important' in task.task_name else 'none'
                }
            )
            if response.status_code == 200:
                task.save_to_db()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Lunist',
                    description='Todoist --> Lunatask task synchronization')
    parser.add_argument('-c', '--config', default="~/.lunist.yaml")
    args = parser.parse_args()

