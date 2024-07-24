from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.form import Form, FormStyleDefault

# index page, includes logic to force users to pick a manager on sign up, 
# the first person signing up will be declared as the 'ceo' and at no point is forced to choose a manager
@action("index", method=["GET","POST"])
@action.uses("index.html", auth.user, session)
def index():
     # get self's id
    user = auth.get_user("id")
    selfUserID = user.get('id')

    #if not auth, then prompt to login 
    if(selfUserID == None):
        redirect(URL('auth/login'))
    
    # get number of total registered users
    rowsAuth = db(db.auth_user).select()      

    # query to find if user is in orgchart
    rowsOrgChartDontCheckManager = db((db.orgchart.user_id == selfUserID) ).select()       

    # query to find if user is in orgchar and has manager
    rowsOrgChartCheckManager = db((db.orgchart.user_id == selfUserID) & 
                      (db.orgchart.manager != None)).select()    
                              

    # if no registered users, prompt a sign up, they will be CEO                                                                
    if(len(rowsAuth) == 0):
        redirect(URL('auth/login'))       
    
    # if there is only 1 registered user in app, then we set them as CEO
    # else if their userID does not have a mngr, and they are not the only user, force to select manager
    if (len(rowsAuth) == 1) :
        if(len(rowsOrgChartDontCheckManager) == 0): #add them to orgchart if there it is empty
            ret = db.orgchart.validate_and_insert(user_id = selfUserID, role='ceo') 
            print(ret)
        return {}
    
    
    #if they are not in orgchar create and send them to choose manager
    if(len(rowsOrgChartDontCheckManager) == 0):
        ret = db.orgchart.validate_and_insert(user_id = selfUserID, role='user') 
        redirect(URL('auth/manager'))

    if (len(rowsOrgChartCheckManager) == 0):
        if(rowsOrgChartDontCheckManager[0].role == 'ceo'):
            return{}
        else:
            redirect(URL('auth/manager'))

    else: #dont think we will ever get here, but just in case
        return{}

#page to edit manager
@action("auth/manager", method=["GET","POST"])
@action.uses("managerEdit.html", db, session, auth.user)
def _():
    # get self's id
    user = auth.get_user("id")
    selfUserID = user.get('id') 
    form = Form(db.orgchart, formstyle=FormStyleDefault)

    # returns all users in auth_user db except self (no self assignment)
    rows = db(db.auth_user.id != selfUserID).select(
            db.auth_user.id, db.auth_user.username, db.auth_user.first_name, db.auth_user.last_name)
    
    return dict(form=form, rows=rows)

# api to set current user's manager to manager_id in orgchart db
@action("api/editManager/<manager_id:int>", method=["GET", "POST"])
@action.uses("generic.html", db, auth, session)
def _(manager_id):
    # get self's id
    user = auth.get_user("id")
    selfUserID = user.get('id') 

    # check if this relationship already exists assignment already exists
    rowsFindAssignmentSelf = db( (db.orgchart.user_id == selfUserID) &
                           (db.orgchart.manager == manager_id) ).select()
    
    # if relationship existed already, simply return to index page
    if( (len(rowsFindAssignmentSelf) > 0)):
        redirect(URL('index'))
    
    # update or insert self into orgchart with manager_id as manager
    ret = db.orgchart.update_or_insert(db.orgchart.user_id == selfUserID,
                                           user_id = selfUserID, role='user', manager = manager_id)

    redirect(URL('index'))

# returns all task ans associated comments, and filters if they are in the request.query
@action("api/tasks", method="GET")
@action.uses(db, auth.user)
def _():
    #if no request query, then return 100 tasks ordered by date
    if(request.query == {}):
        allRows = db(db.task.assigned_to == db.auth_user.id).select(orderby=~db.task.created_on, limitby=(0,100))

    else:
        # pull ALL tasks, will filter them 
        allRows = db(db.task.assigned_to == db.auth_user.id).select(orderby=~db.task.created_on)
        
        #filter rows based on request
        if 'dateCreated' in request.query:
            filterDate = request.query.get('dateCreated')
            allRows = allRows.find(lambda row: str(row.task.created_on)[0:10] in (filterDate))

        if 'deadline' in request.query:
            filterDeadline = request.query.get('deadline')
            allRows = allRows.find(lambda row: str(row.task.deadline)[0:10] in filterDeadline)

        if 'status' in request.query:
            filterStatus = request.query.get('status')
            if filterStatus == 'undefined':
                pass
            else:
                allRows = allRows.find(lambda row: row.task.status == filterStatus)
        
        if 'createdBy' in request.query:
            filterCreatedBy = (request.query.get('createdBy'))
            if filterCreatedBy == 'undefined':
                pass
            else:
                filterCreatedBy = int(filterCreatedBy)
                allRows = allRows.find(lambda row: row.task.created_by == filterCreatedBy)

        if 'assignedTo' in request.query:
            filterAssignedTo = (request.query.get('assignedTo'))
            if filterAssignedTo == 'undefined':
                pass
            else:
                filterAssignedTo = int(filterAssignedTo)
                allRows = allRows.find(lambda row: row.task.assigned_to == filterAssignedTo)
        
        if 'createdByManagedUser' in request.query:
            #get ID
            user = auth.get_user("id")
            selfUserID = user.get('id')
            #find all user ID that this user manages
            rowOfManagedUsers = db(db.orgchart.manager == selfUserID).select(db.orgchart.user_id)

            #create list of managed user ID's
            managedUsersList = []
            for row in rowOfManagedUsers:
                managedUsersList.append(row.user_id)

            allRows = allRows.find(lambda row: int(row.task.created_by) in managedUsersList)
        
        if 'assignedToManagedUsers' in request.query:
            #get ID
            user = auth.get_user("id")
            selfUserID = user.get('id')
            #find all user ID that this user manages
            rowOfManagedUsers = db(db.orgchart.manager == selfUserID).select(db.orgchart.user_id)

            #create list of managed user ID's
            managedUsersList = []
            for row in rowOfManagedUsers:
                managedUsersList.append(row.user_id)

            allRows = allRows.find(lambda row: row.task.assigned_to in managedUsersList)
        
    return {"tasks": allRows.as_list()}

# posts a new task, does nothing if any required fields are left blank
@action("api/tasks", method="POST")
@action.uses("index.html",db, auth.user, flash)
def _():
    data = request.json    
    #validate all required fields are filled
    if( (data.get('title') == "") or (data.get('description') == "") or 
       (data.get('status') == "") or (data.get('deadline') == "")):
        return {}
    else:
        return db.task.validate_and_insert(title=data["title"],
                                        description=data["description"], 
                                        status=data["status"],
                                        deadline=data["deadline"] + " 23:59:59")
    
# api to view a single task and comments associated with that
@action('api/viewTask/<task_id:int>', method='GET')
@action.uses('viewTask.html' ,db, auth.user)
def _(task_id):
    rows = db(db.task.id == task_id).select()
    
    user = auth.get_user("id")
    selfUserID = user.get('id')
    mU = db(db.orgchart.manager == selfUserID).select(db.orgchart.user_id).as_list()
    mU.append({"user_id": auth.get_user("id").get('id')})

    return {"tasks": rows.as_list(), "managedUsers": [user["user_id"] for user in mU], "task_id": task_id}

#api to get all registered user's id, username, first name, last name from DB
@action('api/getUsers', method="GET")
@action.uses(db,auth.user)
def _():
    rows = db(db.auth_user).select(db.auth_user.id, db.auth_user.username, db.auth_user.first_name, db.auth_user.last_name,
                                   orderby=db.auth_user.first_name)
    
    return{"users": rows.as_list()}

#api to get all managed users of person logged in
@action('api/getManagedUsers', method="GET")
@action.uses('generic.html',db,auth.user)
def _():
    user = auth.get_user("id")
    selfUserID = user.get('id')
    rows = db(db.orgchart.manager == selfUserID).select(db.orgchart.user_id)
    
    return{"managedUsers": rows.as_list()}

# api to edit a task
@action("api/tasks/edit/<task_id:int>", method="GET")
@action.uses("editTask.html", db, auth.user)
def _(task_id):    
    assigned = db(db.task.id == task_id).select(db.task.assigned_to).as_list()
    managees = db(db.orgchart.manager == auth.get_user("id").get('id')).select(db.orgchart.user_id).as_list()
    managees.append({"user_id": auth.get_user("id").get('id')})
    mU = [user["user_id"] for user in managees]
    if(len(assigned) <= 0 or assigned[0]["assigned_to"] not in mU):
       redirect(URL('api/viewTask/'+str(task_id)))
    managedUsers = db(db.auth_user.id.belongs(mU)).select(db.auth_user.id, db.auth_user.username, db.auth_user.first_name, db.auth_user.last_name, orderby=db.auth_user.first_name)

    return {"task_id": task_id, "managedUsers": managedUsers}

@action("api/tasks/edit/<task_id:int>", method="PUT")
@action.uses(db, auth.user)
def _(task_id):
    data = request.json
    deadlinetemp = data["deadline"] + " 23:59:59" if (len(data["deadline"].split(" ")) < 2) else data["deadline"]
    return db.task.validate_and_update(task_id, title=data["title"], description=data["description"], status=data["status"], deadline=deadlinetemp, assigned_to=data["assigned_to"])

# api for comments
@action('api/add_comment', method=['POST'])
@action.uses(db, auth.user)
def add_comment():
    user = auth.get_user()
    data = request.json
    task_id = data.get('task_id')
    comment_text = data.get('comment_text')
    
    if not task_id or not comment_text:
        return {"error": "Task ID and comment text are required."}
    
    db.comment.insert(
        task_id=task_id,
        comment=comment_text,
        signature=user['id']
    )
    db.commit()
    return {"success": True, "message": "Comment added successfully."}

@action('api/get_comments/<task_id:int>', method=['GET'])
@action.uses(db, auth.user)
def get_comments(task_id):
    comments = db(db.comment.task_id == task_id).select()
    return {"comments": comments.as_list()}
  