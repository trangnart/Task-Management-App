from datetime import datetime
from py4web import DAL, Field

# Initialize your database connection
db = DAL('sqlite://storage.db')

# Define your tables (if they are not already defined)
db.define_table('tasks',
    Field('title', 'string'),
    Field('description', 'text'),
    Field('status', 'string'),
    Field('created_on', 'datetime'),
    Field('deadline', 'datetime'),
    Field('priority', 'string'),
    Field('notes', 'text'),
    Field('timeline', 'string'),
    Field('created_by', 'reference auth_user'),
    Field('owner_id', 'reference auth_user')
)

# Function to inspect and correct datetime values
def inspect_and_correct_datetimes():
    rows = db(db.tasks).select()
    for row in rows:
        print(f"Task ID {row.id} created_on: {row.created_on}")  # Inspect the created_on field
        if isinstance(row.created_on, str):
            try:
                # Try to convert the string to datetime
                datetime.strptime(row.created_on, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # If conversion fails, correct the format
                print(f"Invalid datetime format for task ID {row.id}: {row.created_on}")
                corrected_datetime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                row.update_record(created_on=corrected_datetime)
                print(f"Corrected datetime for task ID {row.id}: {corrected_datetime}")
    db.commit()

# Run the inspection and correction
inspect_and_correct_datetimes()
