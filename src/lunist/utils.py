#!/usr/bin/env python3
import sqlite3

DB_PATH = './db/tasks.db'

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        task_name TEXT,
        task_description TEXT,
        todoist_id INTEGER UNIQUE,
        lunatask_id INTEGER,
        todoist_project TEXT,
        lunatask_area TEXT,
        priority TEXT,
        in_lunatask BOOLEAN
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subtasks (
        id INTEGER PRIMARY KEY,
        task_id INTEGER,
        subtask_name TEXT,
        subtask_description TEXT,
        FOREIGN KEY(task_id) REFERENCES tasks(id)
    )
    ''')

    conn.commit()
    conn.close()

class Task:
    def __init__(self, task_name, task_description, todoist_id, lunatask_id, todoist_project, lunatask_area, priority, in_lunatask):
        self.task_name = task_name
        self.task_description = task_description
        self.todoist_id = todoist_id
        self.lunatask_id = lunatask_id
        self.todoist_project = todoist_project
        self.lunatask_area = lunatask_area
        self.priority = priority
        self.in_lunatask = in_lunatask

    def save_to_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO tasks (task_name, task_description, todoist_id, lunatask_id, todoist_project, lunatask_area, priority, in_lunatask)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.task_name, self.task_description, self.todoist_id, self.lunatask_id, self.todoist_project, self.lunatask_area, self.priority, self.in_lunatask))
        conn.commit()
        conn.close()

    @staticmethod
    def load_all_tasks():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks')
        tasks = cursor.fetchall()
        conn.close()
        return [Task(*task) for task in tasks]
