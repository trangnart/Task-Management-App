from .common import db, Field, auth
from pydal.validators import IS_DATETIME, IS_NOT_EMPTY, IS_IN_SET, IS_NOT_IN_DB, IS_IN_DB
import datetime
from py4web.utils.grid import Grid
from yatl.helpers import A
from py4web import URL

db.define_table(
    "task",
    Field("title", "string", requires=IS_NOT_EMPTY()),
    Field("description", "string", requires=IS_NOT_EMPTY()),
    Field("deadline", "datetime", requires=IS_DATETIME()),
    Field("status", requires=IS_IN_SET(['pending', 'acknowledged', 'rejected', 'completed', 'failed'])),
    auth.signature, # Adds created_on, created_by, modified_on, modified_by, is_active
    Field("assigned_to", "reference auth_user", requires=IS_IN_DB(db, 'auth_user.id', '%(first_name)s %(last_name)s')),
    Field("post_date", "datetime", writable=False, default=lambda:datetime.datetime.now()),
)

db.define_table(
    "comment",
    Field("description", "text", requires=IS_NOT_EMPTY()),
    Field("task_id", "reference task", requires=IS_NOT_EMPTY()),
    Field("user_id", "reference auth_user", default=auth.user_id, requires=IS_NOT_EMPTY()),
    auth.signature,
)

db.commit()