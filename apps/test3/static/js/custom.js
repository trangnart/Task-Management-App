"use strict";

// utility function to clone an object
function clone(obj) { return JSON.parse(JSON.stringify(obj)); }

// container for everything
var app = {};
// convenience function to make an item
app.make_task = function() {
    return {
        title: "",
        description: "",
        status: "pending",
        deadline: ""
    };
};

// The vue input config object    
app.config = {};
// The vue input setup() function returns the data to be exposed
app.config.setup = function() {
    // used for filtering
    // get call on getUsers api to get all id, first name, last name, and username from auth_users db
    axios.get("../api/getUsers").then(function(res){app.vue.users = res.data.users;});
    
    // // call on getManaged users to get list of id's of managed users
    // axios.get("/task_mgmt/api/getManagedUsers").then(function(res){
    //                     app.vue.managedUsers = res.data.managedUsers;});


    return {
        tasks: Vue.ref([]),
        new_task: Vue.ref(clone(app.make_task())),
        filter_status: "pending",
        filter_deadline: "",
        filter_created_on: "",
        // new vars for comments
        users: Vue.ref([]),
        selected_users: Vue.ref({}),
        new_comment: Vue.ref({}),
        comments: Vue.ref({})
    };
};

// the vue methods to be exposed
app.config.methods = {};
app.config.methods.create_new_task = function() {
    axios.post("../api/tasks", app.vue.new_task).then(function(res){
        //console.log(res.data);
        app.vue.new_task=clone(app.make_task());
        app.reload();
    });
};

app.config.methods.update_task = function(task) {
    axios.put("../api/tasks/edit/"+task.id, task).then(function(res){
        window.location.href = "../api/viewTask/"+task.id;
        app.reload();
    });
};

app.config.methods.show_filtered_tasks = function() {

    let addressVal = "";

    if(this.filter_created_on){
        console.log(this.filter_created_on)
        addressVal += "dateCreated=" + this.filter_created_on + '&';
    }

    if(this.filter_deadline){
        addressVal += "deadline=" + this.filter_deadline + '&';
    }
    
    if(this.filter_status != 'undefined'){
        addressVal += "status=" + this.filter_status + '&';
    }

    if(this.filter_createdBy != 'undefined'){
        addressVal += "createdBy=" + this.filter_createdBy + '&';
    }

    if(this.filter_assignedTo != 'undefined'){
        addressVal += "assignedTo=" + this.filter_assignedTo + '&';
    }

    if(this.filter_createdByManagedUsers){
        addressVal += "createdByManagedUser=true&";
    }

    if(this.filter_assignedToManagedUsers){
        addressVal += "assignedToManagedUsers=true";
    }

    if(addressVal != ""){
        axios.get("../api/tasks?" + addressVal).then(function(res){
            app.vue.tasks = res.data.tasks;
        });
    }else{
        axios.get("../api/tasks").then(function(res){ app.vue.tasks = res.data.tasks; });
    }
};

// comment functions
app.config.methods.add_comment = function(task_id) {
    let comment_text = this.new_comment[task_id];
    if (!comment_text) {
        return;
    }
    axios.post('../api/add_comment', {
        task_id: task_id,
        comment_text: comment_text
    }).then(response => {
        if (response.data.success) {
            this.fetch_comments(task_id);
            this.new_comment[task_id] = ''; // Clear the input after successful comment submission
        } else {
            console.error(response.data.error);
        }
    }).catch(error => {
        console.error('Error adding comment:', error);
    });
};

app.config.methods.fetch_comments = function(task_id) {
    axios.get(`../api/get_comments/${task_id}`).then(response => {
        this.comments[task_id] = response.data.comments;
    }).catch(error => {
        console.error('Error fetching comments:', error);
    });
};

app.config.methods.fetch_all_comments = function() {
    this.tasks.forEach(task => {
        this.fetch_comments(task.task.id);
    });
};

app.reload = function() {
    // then reload any saved data
    // axios.get("/task_mgmt/api/tasks").then(function(res){ app.vue.tasks = res.data.tasks; });
    axios.get("../api/tasks").then(function(res) { 
        app.vue.tasks = res.data.tasks; 
        app.vue.fetch_all_comments();
    });
};


// make the vue app
app.vue = Vue.createApp(app.config).mount("#app");
app.reload();