## Final Project for Web Application (UCSC)

The project consists of creating a task management app. Tasks have a title, a desciption, a signature (created_on, created_by), a deadline, and a status (pending, ackowledged, rejected, completed, failed). Task also have comments.

You create tasks and assign them to yourself and/or other users. Every user must have a manager (another user), except the CEO, and every user can edit their own tasks as well the tasks created by people he/she manages.
Every user should be able to:
- select and change own manager
- create a task
- see all the tasks
- edit a task (any field) but only if created by self or a managed person (important!)
- add a comment to any task
- filter tasks by:
  - date created
  - deadline
  - status
  - created by self
  - assigned to self
  - created by a specific user
  - assigned to a specific user
  - created by any managed user
  - assigned to any managed user

You must use py4web. Vue is optional.