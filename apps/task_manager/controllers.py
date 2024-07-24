from py4web import action, request, abort, redirect, URL
from py4web.utils.form import Form
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
import re
from datetime import datetime

#Endpoint for index page and login page
@action('index') 
@action.uses("index.html", db, auth.user)
def index():
#    tasks = db(db.).select(orderby=~db..created_on, limitby=(0,100))
    return locals()

# Endpoint to create a new task using the POST method
@action("api/tasks", method="POST")
@action.uses(db, auth.user)
def _(): 
    data = request.json
    deadline = datetime.strptime(data["deadline"], '%Y-%m-%d')
    data["deadline"] = deadline
    result = db.task_item.validate_and_insert(**data)  
    return {"errors": result}
  
# Endpoint for updating a task using the PUT method
@action("api/tasks/<task_id>", method="PUT")
@action.uses(db, auth.user)
def _(task_id):    
    data = request.json # getting all the new data 
    current_record = db.task_item[task_id]
    new_title = data["title"]
    new_description = data["description"]
    new_assigned_to = data["assigned_to"]
    new_status = data["status"]
    new_deadline = data["deadline"]

      # updated_record bypasses validation but only changes the fields you pass in!
    result = current_record.update_record(
        title=new_title, description=new_description, assigned_to=new_assigned_to, status=new_status,
        deadline=new_deadline
    )
    return {"updates task": task_id}

# Endpoint for commenting a task using the POST method
@action("api/tasks/<task_id>/comments/", method="POST")
@action.uses(db, auth.user)
def _(task_id): 
    data = request.json
    result = db.task_comments.validate_and_insert(**data)
    return {"result": result}

# Endpoint for adding/update manager information
@action("api/managers", method="PUT")
@action.uses(db, auth.user)
def _():
    data = request.json
    # check to make sure an entry for a user is created in the manager table
    if data["manager"] == "":
        rows = db(db.managers.user == data["user"]).select().as_list()
        if len(rows) > 0:
            return {}
        
    if data["manager"] == "reset":
        data["manager"] = ""
    
    result = db.managers.update_or_insert(db.managers.user == data["user"], user=data["user"], manager=data["manager"])
    return {"result": result}

"""
GET ENDPOINTS 
"""
# Endpoint to fetch all tasks, with optional filters using the GET method
@action("api/tasks", method="GET")
@action.uses(db, auth.user)
def _(): 
    query = (db.task_item.status != "")
    created_on = request.params.get("created_on")
    deadline = request.params.get("deadline")
    status = request.params.get("status")
    created_by = request.params.get("created_by")
    created_by_user = request.params.get("created_by_user")
    assigned_to = request.params.get("assigned_to")
    created_by_managed = request.params.get("created_by_managed")
    assigned_to_managed = request.params.get("assigned_to_managed")
    # Get all tasks, filtered by date created
    if created_on:
        created_on_date = datetime.strptime(created_on, '%m-%d-%Y')
        query &= (db.task_item.created_on.year() == created_on_date.year)
        query &= (db.task_item.created_on.month() == created_on_date.month)
        query &= (db.task_item.created_on.day() == created_on_date.day)

    # Get all tasks, filtered by deadline
    if deadline:
        deadline_date = datetime.strptime(deadline, '%m-%d-%Y')
        query &= (db.task_item.deadline.year() == deadline_date.year)
        query &= (db.task_item.deadline.month() == deadline_date.month)
        query &= (db.task_item.deadline.day() == deadline_date.day)
       
    # Get all tasks, filtered by status: ['pending','ackowledged','rejected','completed','failed']
    if status:
        query &= (db.task_item.status == status)

    # Get all tasks, filtered by created by self or by a specific user
    if created_by:
        query &= (db.task_item.created_by == created_by)   
    if created_by_user:
        query &= (db.task_item.created_by_user == created_by_user)

    # Get all tasks assigned to a specific user
    if assigned_to:
        query &= (db.task_item.assigned_to == assigned_to)

    # Get all tasks created by teammates
    if created_by_managed:
        manager_id = auth.user_id
        team_rows = db(db.my_team.manager == manager_id).select()
        team_members = set()
        for row in team_rows:
            team_members.update(row.team)
        team_members.add(manager_id)
        query &= db.task_item.created_by.belongs(team_members)

     # Get all tasks assigned teammates
    if assigned_to_managed:
        manager_id = auth.user_id
        team_rows = db(db.my_team.manager == manager_id).select()
        team_members = set()
        for row in team_rows:
            team_members.update(row.team)
        team_members.add(manager_id)
        query &= db.task_item.assigned_to.belongs(team_members)
        # this is the line causing problems at the moment
    
    rows = db(query).select(orderby=~db.task_item.created_on).as_list()

    # this section is to return the users
    user_query = (db.auth_user.id >= 0)
    users = db(user_query).select().as_list()

    # this section is to get the identity of the logged in user
    user = auth.get_user()

    return {"tasks": rows, "users": users, "user": user}

# Endpoint for fetching comments using the GET method
@action("api/tasks/<task_id>/comments", method="GET")
@action.uses(db, auth.user)
def _(task_id):
    rows = db(db.task_comments.task_item_id == task_id).select().as_list()
    return {"comments": rows}

@action("api/managers/<user_id>", method="GET")
@action.uses(db, auth.user)
def _(user_id):
    entry = db(db.managers.user == user_id).select().as_list()
    managed_entries = db(db.managers.manager == user_id).select().as_list()
    managed_users = []
    for i in managed_entries:
        managed_users.append(i["user"])
    return {"manager": entry[0], "managed": managed_users}
    # return {"manager": ""}

# Endpoint for deleting tasks using the DELETE method
@action("api/tasks/<task_id>", method="DELETE")
@action.uses(db, auth.user)
#@action.uses(auth.user)
def _(task_id):
    db(db.task_item.id == task_id).delete()
    return {}