"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""


from py4web import action, request, abort, redirect, URL, Field
from yatl.helpers import A
from py4web.utils.form import Form, FormStyleBulma
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from pydal.validators import IS_IN_SET, IS_IN_DB
from py4web.utils.grid import URL
from py4web.utils.grid import *


@action("index")
@action.uses("index.html", auth, T)
def index():
    redirect(URL('tasks'))

@action("tasks/create", method=["GET", "POST"])
@action.uses("task_form.html", auth.user, db)
def create_task():
    db.task.assigned_to.requires = IS_IN_DB(db, 'auth_user.id', '%(first_name)s %(last_name)s')
    form = Form(db.task, formstyle=FormStyleBulma)
    if form.accepted:
        redirect(URL('tasks'))
    return dict(form=form)

# @action("custom_register", method=["GET", "POST"])
# @action.uses(session, db, T, auth, "auth.html")
# def register():
#     auth.param.formstyle = FormStyleBulma
#     form = auth.register_form(extra_fields=[Field("role", requires=IS_IN_SET(['CEO', 'User']), label="Role")])
#     return dict(form=form)

# GET ROLE
@action("tasks/get_role", method=["GET"])
@action.uses(db)
def get_role():
    user = auth.get_user()
    role = user.get("role") if user else None
    return dict(role= role)

# GET MANAGER
@action("tasks/get_manager", method="GET")
@action.uses(db)
def get_manager():
    user = auth.get_user()
    current_manager = user.get('managed_by') if user else None
    return dict(managed_by= current_manager)

@action("tasks/get_managed", method="GET")
@action.uses(db)
def get_managed():
    user = auth.get_user()
    if(user):
        current_managed= db(db.auth_user.managed_by == user["email"]).select(db.auth_user.id)
        current_managed= [row.id for row in current_managed]
        return dict(current_managed = current_managed)
    return dict(current_managed = [])

# UPDATE MANAGER
@action("tasks/update_manager", method=["POST"])
def update_manager():

    user_id = request.params.get("user_id")
    new_manager = request.params.get("manager")

    # Update the managed_by field for the specified user_id
    db(db.auth_user.id == user_id).update(managed_by=new_manager)

    # Redirect
    redirect(URL('tasks'))

# GET ALL EMAILS
@action("tasks/emails", method="GET")
@action.uses(db)
def get_emails():
    user = auth.get_user()
    if(user):
        emails = [user.email for user in db(db.auth_user).select(db.auth_user.email)]
        emails.remove(user["email"])
        return dict(emails=emails)
    return dict(emails = [])

class GridActionButton:
    def __init__(
        self,
        url,
        text=None,
        icon=None,
        additional_classes="",
        message="",
        append_id=False,
        ignore_attribute_plugin=False,
    ):
        self.url = url
        self.text = text
        self.icon = icon
        self.additional_classes = additional_classes
        self.message = message
        self.append_id = append_id
        self.ignore_attribute_plugin = ignore_attribute_plugin

@action("tasks", method=["GET", "POST"])
@action("tasks/<path:path>", method=["GET", "POST"])
@action.uses("task.html", auth.user, db, session)
def tasks(path=None):
    user = auth.get_user()
    db.task.title.label = "Task"
    db.task.description.label = "Task Description"
    db.task.post_date.label = "Created on"
    db.task.created_on.readable=False
    db.task.created_by.readable=False
    db.task.modified_on.readable=False
    db.task.modified_by.readable=False
    emails = get_emails()["emails"]
    managed_by = get_manager()["managed_by"]
    role = get_role()["role"]
    current_managed=get_managed()["current_managed"]

    
    def comment_button(row):
        return GridActionButton(
            url=URL('tasks/comment', row.id),
            text='Comments',
            icon='fa-comment',
            additional_classes='button is-info is-small',
            )
    pre_action_buttons = [comment_button]
    
    # only allow person that made the task OR is a manager to edit the task 
    if path and path.startswith("edit/"):
        task_id = path.split("/")[-1]
        task = db.task(task_id)
        if task and (task.created_by == auth.user_id or (user and task.created_by in current_managed)):
            form = Form(db.task, record=task, deletable=False, formstyle=FormStyleBulma)
            if form.accepted:
                redirect(URL("tasks"))
            return dict(form=form, emails=emails, managed_by=managed_by, role=role)
        else:
            redirect(URL("tasks"))

    # delete only if created task or is a manager
    if path and path.startswith("delete/"):
        task_id = path.split("/")[-1]
        task = db.task(task_id)
        if task and (task.created_by == auth.user_id or (user and task.created_by in current_managed)):
            db(db.task.id == task_id).delete()
            redirect(URL("tasks"))
        else:
            redirect(URL("tasks"))

    #removed db.task.user_id. caused an error.
    fields = [db.task.id,
              db.task.title,
              db.task.description, db.task.post_date,
              db.task.deadline, db.task.status, db.task.assigned_to, db.task.created_by]

    # Define search queries
    search_queries = [
        ["title", lambda value: db.task.title.contains(value)],
        ["description", lambda value: db.task.description.contains(value)],
        #["date created", lambda value: db.task.created_on == datetime.datetime.strptime(value, "%m/%d/%Y, %I:%M:%S %p")],
        #["deadline", lambda value: db.task.deadline == datetime.datetime.strptime(value, "%m/%d/%Y, %I:%M:%S %p")],
        ["status", lambda value: db.task.status.contains(value)],
        ["created by", lambda value: db.auth_user.first_name.contains(value) | db.auth_user.last_name.contains(value)],
        ["assigned to", lambda value: db.auth_user.first_name.contains(value) | db.auth_user.last_name.contains(value)],
    ]

    grid = Grid(
        path,
        db.task,
        details=False,
        create=False,
        fields=fields,
        formstyle=FormStyleBulma,
        grid_class_style=GridClassStyleBulma,
        search_queries=search_queries,
        rows_per_page=10,
        pre_action_buttons=pre_action_buttons,
        left=db.auth_user.on(db.task.created_by == db.auth_user.id)
    )

    return dict(grid=grid, user=user, emails=emails,
                managed_by=managed_by, role=role)
    #return locals()


#comments

@action("tasks/comment/<task_id:int>", method=["GET", "POST"])
@action.uses("comment.html", auth.user, db, session)
def comment(task_id):
    task = db.task[task_id]
    if not task:
        redirect(URL("tasks"))

    comments = db(db.comment.task_id == task_id).select(
        db.comment.ALL,
        db.auth_user.first_name,
        db.auth_user.last_name,
        left=db.auth_user.on(db.comment.user_id == db.auth_user.id),
        orderby=~db.comment.id,
    )
    return dict(comments=comments, task=task)

@action("tasks/add_comment/<task_id:int>", method=["POST"])
@action.uses(auth.user, db)
def add_comment(task_id):
    task = db.task[task_id]
    if not task:
        return dict(success=False, message="Task not found")

    comment_data = request.json
    comment_id = db.comment.insert(
        description=comment_data["description"],
        task_id=task_id,
        user_id=auth.user_id,
    )

    comment = db.comment[comment_id]
    user = db.auth_user[comment.user_id]

    return dict(
        success=True,
        comment=dict(
            id=comment.id,
            description=comment.description,
            user_name=f"{user.first_name} {user.last_name}",
            created_on=comment.created_on.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )




