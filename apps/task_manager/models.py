from .common import db, Field, auth
from pydal.validators import *
import datetime

#CITATIONS:
# Use of IS-IN-SET: https://py4web.com/_documentation/static/en/chapter-12.html#is-in-set

#Table for tasks
db.define_table(
    "task_item",

    #id for each task
    Field("id", "integer", requires=IS_NOT_EMPTY(), default=0),

    # must have a title
    Field("title", "string", requires=IS_NOT_EMPTY()),

    # must have a description
    Field("description", "string", requires=IS_NOT_EMPTY()),
   
    # tasks needs a status
    Field("status",  options=(['Pending','Acknowledged','Rejected','Completed','Failed']), default="Pending"),
    
    # task needs a "deadline"
    Field("deadline", "datetime", readable=False, writable=True, default=lambda:datetime.datetime.now() + datetime.timedelta(hours=24)),
    
    # tasks needs a  "assigned to"
    Field("assigned_to", "string", requires=IS_NOT_EMPTY()),
    
    #tasks needs a created_on and created_by
    auth.signature,
)

#Table for handling managers
db.define_table(
    "managers",
    # a reference to a user
    Field("user", "reference auth_user"),

    # the manager of the user
    Field("manager", "reference auth_user")
)

#Table for handling comments 
db.define_table(
    "task_comments",

    # reference to the task
    Field("task_item_id", "reference task_item"),

    # the actual comment
    Field("content", "string"),
    
    # whoever is writing the comment
    Field("author", "reference auth_user", requires=IS_NOT_EMPTY())
)

db.commit()