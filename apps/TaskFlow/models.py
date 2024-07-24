from .common import db, Field
from py4web.utils.auth import Auth
from py4web import Session
from pydal.validators import IS_EMPTY_OR, IS_IN_DB, IS_IN_SET, IS_NOT_EMPTY, IS_DATETIME
import os
from datetime import datetime

print("Starting models.py initialization")

# Generate a proper secret for the session
secret = os.urandom(32).hex()  # Convert to hex to make it a valid string
print(f"Session secret generated: {secret}")

# Initialize Session with a proper secret
session = Session(secret=secret)
print("Session initialized")

# Initialize Auth with the database and session
auth = Auth(session, db=db)
print("Auth initialized")

# Define the auth tables
auth.define_tables()
print("Auth tables defined")

# Define the Managers table
db.define_table('user_manager',
    Field('user_id', 'reference auth_user', unique=True),
    Field('manager_id', 'reference auth_user', requires=IS_EMPTY_OR(IS_IN_DB(db, 'auth_user.id', '%(email)s')))
)
print("User Manager table defined")

# Define the Tasks table
db.define_table('tasks',
    Field('title', 'string'),
    Field('description', 'text'),
   Field('comment_text', 'text'), 
    Field('status', 'string', requires=IS_IN_SET(['pending', 'acknowledged', 'rejected', 'completed', 'failed'])),
    Field('created_on', 'datetime', default=datetime.now()),
    Field('priority', 'string', requires=IS_IN_SET(['Low', 'Medium', 'High'])),
    Field('deadline', 'datetime', default=None, null=True),
    Field('created_by', 'reference auth_user'),
    Field('assigned_to', 'reference auth_user', default=None, null=True))

print("Tasks table defined")

# Define the Comments table
db.define_table('comments',
    Field('task_id', 'reference tasks'),
    Field('user_id', 'reference auth_user'),
    Field('content', 'text'),
    Field('created_on', 'datetime', default=datetime.utcnow, requires=IS_DATETIME('%Y-%m-%d %H:%M:%S'))
)
print("Comments table defined")

# Commit the database changes
db.commit()
print("Database schema committed")

# Print the database path
db_path = db._uri.split('://')[1]  # Get the path to the SQLite database
print(f"Database path: {db_path}")

print("Finished models.py initialization")