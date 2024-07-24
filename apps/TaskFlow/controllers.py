

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web import action, request, response, abort
from .models import db
from pydal.validators import *
from py4web.utils.form import Form, FormStyleBulma
import json
import datetime
from datetime import timedelta


@action("feed")
@action.uses("feed.html", auth, T)
def feed():
    print("inside feeddddd")
    user_id = auth.current_user.get('id')
    if not user_id:
        redirect(URL('index'))  # Or your login page

    # Fetch tasks associated with the user
    print("fetch tasks")
    tasks = db(db.tasks.created_by == user_id).select()
    print(tasks)
  
    return dict(tasks=tasks) 



@action("index")
@action.uses("index.html", auth, T)
def index():

    message = T("Welcome to TaskFlow")  # Generic welcome messag
    user = auth.get_user()
    if user:
        redirect(URL('feed'))
    message = T("Hello {first_name}").format(**user) if user else T("Hello")
    return dict(message=message)


def allow_cors(func):
    def wrapper(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept'
        if request.method == 'OPTIONS':
            return response.json({'status': 'ok'}, status=200)
        return func(*args, **kwargs)
    return wrapper


@action('api/tasks', method=['GET'])
@action.uses(db, auth)
def get_tasks():
    print("inside get tasks")
    user = auth.current_user
    if not user:
        return dict(tasks=[])

    filters = request.query
    if filters:
        print("filters",filters)
        query = (db.tasks.id > 0)

        if 'status' in filters:
            query &= (db.tasks.status == filters['status'])
        if 'created_by' in filters:
            print('inside craeted by')
            query &= (db.tasks.created_by == user['id'])
        if 'assigned_to' in filters:
            query &= (db.tasks.assigned_to == user['id'])
        if 'specific_user' in filters:
            specific_user = filters['specific_user']
            query &= ((db.auth_user.email.contains(specific_user)) & 
                    ((db.tasks.created_by == db.auth_user.id) | 
                    (db.tasks.assigned_to == db.auth_user.id)))
        if 'managed_user' in filters:
            managed_user_ids = [row.id for row in db(db.auth_user.manager == user['id']).select()]
            query &= (db.tasks.created_by.belongs(managed_user_ids) | db.tasks.assigned_to.belongs(managed_user_ids))
        if 'date_created' in filters:
            print('created on')
            date_created_str = filters['date_created']
            date_created = datetime.strptime(date_created_str, '%Y-%m-%d')
            query &= (db.tasks.created_on >= date_created) & (db.tasks.created_on < date_created + timedelta(days=1))

        if 'deadline' in filters:
            print('deadline')
            deadline_str = filters['deadline']
            deadline = datetime.strptime(filters['deadline'], '%Y-%m-%dT%H:%M:%SZ')
            query &= (db.tasks.deadline <= deadline)

        tasks = db(query).select().as_list()
    else:
        print("no filter")
        tasks = db(db.tasks).select().as_list()
        for task in tasks:
            print(task)  # Debug log to print each task
    
    return dict(tasks=tasks)

# Add similar endpoints for other filters as needed

@action('api/tasks', method=['POST'])
@action.uses(db, auth.user)
def api_create_task():
    print('inside create')
    data = request.json
    print(data)
    if not data or 'title' not in data or 'description' not in data or 'priority' not in data:
        response.status = 400
        return {'error': 'Missing data'}

    created_by = auth.current_user.get('id')
    if not created_by:
        response.status = 400
        return {'error': 'User not authenticated'}

    assigned_to = data.get('assigned_to')
    print('task assigned to', assigned_to)
    if assigned_to:
        if not db(db.auth_user.id == assigned_to).select().first():
            response.status = 400
            return {'error': 'Invalid assigned_to'}
    else:
        assigned_to = None  # Explicitly set assigned_to to None if not provided

    print('hi')

    # Handle deadline
    deadline = data.get('deadline')
    if deadline == '':
        deadline = None
    else:
        try:
            deadline = datetime.datetime.strptime(deadline, '%Y-%m-%dT%H:%M')
        except ValueError:
            response.status = 400
            return {'error': 'Invalid deadline format'}

    try:
        print('insert')
        task_id = db.tasks.insert(
            title=data['title'],
            description=data['description'],
            status=data.get('status', 'pending'),
            priority=data['priority'],
            created_on=datetime.datetime.utcnow(),
            deadline=deadline,
            created_by=created_by,
            assigned_to=assigned_to
        )
        print('commit')
        db.commit()
        return {'task_id': task_id}
    except Exception as e:
        print(f"Error inserting task: {e}")
        response.status = 500
        return {'error': 'Internal server error'}


@action('api/tasks/<task_id:int>', method=['DELETE'])
@allow_cors
def api_delete_task(task_id):
    task = db.tasks(task_id)
    if not task:
        abort(404, 'Task not found')
    task.delete_record()
    db.commit()
    return {response.status: 'success'}




@action('api/update_manager', method=['POST'])
@action.uses(db, auth.user)
def update_manager():
    user_id = auth.current_user.get('id')
    data = request.json

    print("Received request data:", data)
    
    if data is None:
        response.status = 400
        print("Error: No data provided")
        return {'error': 'No data provided'}
    
    new_manager_id = data.get('manager_id')

    if new_manager_id is None:
        response.status = 400
        print("Error: Missing manager_id")
        return {'error': 'Missing manager_id'}

    # Debug: Print user_id and new_manager_id to verify values
    print(f"Updating manager for user_id: {user_id} to new_manager_id: {new_manager_id}")

    # Ensure user_id and new_manager_id are integers
    try:
        user_id = int(user_id)
        new_manager_id = int(new_manager_id)
    except ValueError:
        response.status = 400
        print("Error: Invalid user ID or manager ID")
        return {'error': 'Invalid user ID or manager ID'}

    # Debug: Check if user exists
    print("Debug: Check if user exists")
    user = db(db.auth_user.id == user_id).select().first()
    print("User found:", user)

    if user is None:
        response.status = 400
        print(f"Error: User not found for user_id: {user_id}")
        return {'error': 'User not found'}

    # Debug: Check if new manager exists
    new_manager = db(db.auth_user.id == new_manager_id).select().first()
    print("New manager found:", new_manager)
    if new_manager is None:
        response.status = 400
        print(f"Error: New manager not found for new_manager_id: {new_manager_id}")
        return {'error': 'New manager not found'}

    # Update or insert the manager relationship
    db.user_manager.update_or_insert(
        db.user_manager.user_id == user_id,
        user_id=user_id,
        manager_id=new_manager_id
    )
    db.commit()

    print("Manager updated successfully")
    return {'status': 'success'}


@action('api/users', method=['GET'])
@action.uses(db, auth.user)
def api_get_users():
    print('inside get users')
    users = db(db.auth_user).select(db.auth_user.id, db.auth_user.email).as_list()
    print(users)
    return {'users': users}



@action('api/current_user', method=['GET'])
@action.uses(db, auth.user)
def api_current_user():
    user = auth.current_user
    if user:
        user_info = {
            'id': user.get('id'),
            'username': user.get('username'),
            'email': user.get('email'),
            'first_name': user.get('first_name'),
            'last_name': user.get('last_name')
        }
        return dict(user=user_info)
    else:
        response.status = 401
        return dict(error="User not logged in")
    


def is_managed_by(user_id, manager_id):
    print('inside is_managed_by')
    # Check if the user is managed by the manager
    return db(db.user_manager.user_id == user_id and db.user_manager.manager_id == manager_id).select().first()

@action('api/tasks/<task_id:int>', method=['PUT'])
@action.uses(db, auth.user)
def api_edit_task(task_id):
    print('inside edit')
    data = request.json
    print(data)
    if not data:
        response.status = 400
        return {'error': 'Missing data'}

    user_id = auth.current_user.get('id')
    if not user_id:
        response.status = 400
        return {'error': 'User not authenticated'}

    task = db.tasks(task_id)
    if not task:
        abort(404, 'Task not found')

    if task.created_by != user_id and not is_managed_by(task.created_by, user_id):
        response.status = 403
        return {'error': 'Permission denied'}
    print('hi')
    # Handle deadline
    deadline = data.get('deadline')
    print(deadline)
    if deadline:
        try:
            # Attempt to parse with full datetime format
            deadline = datetime.datetime.strptime(deadline, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            try:
                # Attempt to parse without seconds
                deadline = datetime.datetime.strptime(deadline, '%Y-%m-%dT%H:%M')
            except ValueError as e:
                print('problem ')
                print(f"Error updating deadline: {e}")
                response.status = 400
                return {'error': 'Invalid deadline format'}
    else:
        deadline = task.deadline
    print('deadline done')
    try:
        task.update_record(
            title=data.get('title', task.title),
            description=data.get('description', task.description),
            status=data.get('status', task.status),
            priority=data.get('priority', task.priority),
            deadline=deadline,
            assigned_to=data.get('assigned_to', task.assigned_to)
        )
        db.commit()
        return {'status': 'success'}
    except Exception as e:
        print(f"Error updating task: {e}")
        response.status = 500
        return {'error': 'Internal server error'}
    




# Endpoint to fetch comments for a specific task
@action('api/tasks/<task_id:int>/comments', method=['GET'])
@action.uses(db, auth.user)
def api_get_comments(task_id):
    print('inside get comment')
    comments = db(db.comments.task_id == task_id).select().as_list()
    print(comments)
    return dict(comments=comments)

@action('api/tasks/<task_id:int>/comments', method=['POST'])
@action.uses(db, auth.user)
def api_create_comment(task_id):
    print('inside create comment')
    data = request.json
    if not data or 'comment_text' not in data:
        response.status = 400
        return {'error': 'Missing comment text'}
    
    created_by = auth.current_user.get('id')
    if not created_by:
        response.status = 400
        return {'error': 'User not authenticated'}
    
    comment_text = data['comment_text']
    current_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    try:
        task = db.tasks(task_id)
        if not task:
            response.status = 404
            return {'error': 'Task not found'}
        
        # Append new comment to existing comments
        if task.comment_text:
            new_comment_text = f"{task.comment_text}\n[{current_time}] {comment_text}"
        else:
            new_comment_text = f"[{current_time}] {comment_text}"
        
        task.update_record(comment_text=new_comment_text)
        db.commit()
        return {'status': 'success'}
    except Exception as e:
        print(f"Error inserting comment: {e}")
        response.status = 500
        return {'error': 'Internal server error'}