"""
This file defines the database models
"""

from .common import db, Field, auth
from pydal.validators import *
import datetime

### Definition for OrgChart Table
#

db.define_table(
    "orgchart", 
    Field("user_id", "reference auth_user", unique=True, default=lambda:auth.user_id, requires=IS_NOT_EMPTY()),
    Field("role", options=("user", "manager", "ceo")),
    Field("manager", "references auth_user"),
    Field("manages", "references auth_user")
)

db.define_table(
    "task",
    Field("title", requires=IS_NOT_EMPTY()),
    Field("description", "text", requires=IS_NOT_EMPTY()),
    Field("created_on", "datetime", readable=False, writable=False, default=lambda:datetime.datetime.now()),
    Field("created_by", "reference auth_user", default=lambda:auth.user_id),
    Field("deadline", "datetime", readable=True, writable=True, requires=IS_NOT_EMPTY()),
    Field("assigned_to", "reference auth_user", default=lambda:auth.user_id, requires=IS_NOT_EMPTY()),
    Field("status", options=("pending", "acknowledged", "rejected", "completed", "failed"), default="pending")
)

db.define_table(
    "comment",
    Field("task_id", "reference task"),
    Field("comment", "text", requires=IS_NOT_EMPTY()),
    Field("signature", "reference auth_user", writable=False, default=lambda:auth.user_id)
)
