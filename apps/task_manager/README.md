# Welcome to Task Manager!

Created by Sophie Hernandez, Shreya Sundar, Stephen Sun, Dexter Zhang

## What is Task Manager?

A task management app, where the user can create and assign tasks to one another. Our web app is designed for versatility and ease of use, with all features conveniently handled on a single page.

Key Features:

- Users can select and change their own manager
- Able to create/add/edit/remove tasks from a task board
- Give a title and description for the task
- Set status (pending, ackowledged, rejected, completed, failed) of task
- Set deadline for the task
- Set a signature (created_on, created_by) for the task
- Users can leave a comment on specific assigned task

## How to Run the Web App?

To be able to try Task Manager please go to 127.0.0.1:8000/task_manager

- Make sure to delete your database before running it, for the best experience with Task Manager
- If you run the web app, and you so happen to be brought to the homepage right away you will not be able to create/add/edit/delete a task without being logged in. To login, look at the top right hand corner that says "Login" to be able to do so.

## Some limitations of the Web App

Though our web app is ease of use, there are some limitations that users should be aware about when creating/adding/editing/removing tasks on the site.

- Can only run one filter at a time, as of right now it does not work for selecting multiple filters at once.
- When choosing who to assign a task to, as of right now you can only choose yourself or any user's who you have added to the auth_user database.
- When editing a post, the created/modified by information might disappear
