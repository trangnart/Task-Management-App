"use strict";

// utility function to clone an object
function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

//new main application object
var app = {};

//Defining a new empty task template
(app.empty_new_task = {
  title: "",
  description: "",
  status: "",
  deadline: "",
  assigned_to: "",
}),
  //Config for Vue instance
  (app.config = {
    // Function to initialize the data properties
    data: function () {
      return {
        new_task: clone(app.empty_new_task),
        current_user: {},
        tasks: [],
        users: [],
        managed: [],
        manager: "",
        new_comment: "",
        comments: {},
        //Boolean for dropdown state
        manager_dropdown: false,
        status_dropdown: false,
        created_dropdown: false,
        deadline_dropdown: false,
        created_by_dropdown: false,
        assigned_to_dropdown: false,
        //Filters for filtering functionality
        filters: {
          created_on: "",
          created_by: "",
          created_by_user: "",
          status: "",
          deadline: "",
          assigned_to: "",
          created_by_managed: "",
          assigned_to_managed: "",
        },
        //Current Editing State
        editing: { current: null },
      };
    },
    methods: {
      reload: function () {
        app.load_data();
      },

      //method to add a new task
      add_task: function () {
        this.cancel();
        let task = clone(this.new_task);
        // Posting to controllers
        axios
          .post("/task_manager/api/tasks", task)
          .then((res) => {
            task.id = res.data.id;
            //reset new task form
            app.vue.new_task = clone(app.empty_new_task);
            // Move the task to the top of the feed
            app.vue.tasks.unshift(task);
            //Resetting the new task and loading the data
            this.new_task = app.empty_new_task;
            app.load_data();
          })
          .catch(function (error) {
            // Display error message to the user
            alert("Invalid Field");
          });
      },
      //method to update manager info
      post_manager: function (user_id, manager_id) {
        let manager_info = {
          user: user_id,
          manager: manager_id,
        };
        axios.put("/task_manager/api/managers", manager_info);
      },
      //method to edit a task
      edit: function (task) {
        this.cancel();
        this.editing = { current: task, old: clone(task) };
      },
      //method to save a task
      save: function (task) {
        task = clone(task);
        // Updating task on controllers
        axios.put(`/task_manager/api/tasks/${task.id}`, task);
        this.editing = { current: null };
      },
      //method to cancel an edit of a task
      cancel: function () {
        //On the the edited task, restore the old task
        if (this.editing.current)
          for (var key in this.editing.current)
            this.editing.current[key] = this.editing.old[key];
        this.editing = { current: null };
      },
      //method to add comments to a task
      add_comment: function (id) {
        let comment = this.new_comment;
        let req = {
          task_item_id: id,
          content: comment,
          author: this.current_user.id,
        };
        //Posting comment to the controllers
        axios
          .post(`/task_manager/api/tasks/${id}/comments`, req)
          .then((res) => {
            // here we are able to use this.new_comment to correctly refer to the
            // same this.new_comment we used earlier because normal functions create their own 'this'
            // context but arrow functions do not that's how I am able to avoid scope issues.
            this.new_comment = "";
            this.get_comments(id);
          });
      },
      //method to retrieve comments
      get_comments: function (id) {
        axios.get(`/task_manager/api/tasks/${id}/comments`).then((res) => {
          this.comments[id] = res.data.comments;
        });
      },
      //method to delete task
      delete_task: function (id) {
        axios.delete(`/task_manager/api/tasks/${id}`).then(function (res) {
          // Remove task with the id
          app.vue.tasks = app.vue.tasks.filter((task) => task.id != id);
          app.load_data();
        });
        app.load_data();
      },
    },
  });

//Function to load the data for the filter buttons
app.load_data = function () {
  let queryString = "";
  // created_on
  if (app.vue.filters.created_on) {
    queryString += `created_on=${app.vue.filters.created_on}&`;
    // deadline
  } else if (app.vue.filters.deadline) {
    queryString += `deadline=${app.vue.filters.deadline}&`;
    // status
  } else if (app.vue.filters.status) {
    queryString += `status=${app.vue.filters.status}&`;
    // created_by
  } else if (app.vue.filters.created_by) {
    queryString += `created_by=${app.vue.filters.created_by}&`;
    // assigned_to_user
  } else if (app.vue.filters.assigned_to) {
    queryString += `assigned_to=${app.vue.filters.assigned_to}&S`;
    // created_by_user
  } else if (app.vue.filters.created_by_user) {
    queryString += `created_by_user=${app.vue.filters.created_by_user}&`;
    // created_by_managed
  } else if (app.vue.filters.created_by_managed) {
    queryString += `created_by_managed=${app.vue.filters.created_by_managed}&`;
    // assigned_to_managed
  } else if (app.vue.filters.assigned_to_managed) {
    queryString += `assigned_to_managed=${app.vue.filters.assigned_to_managed}&`;
  }

  if (queryString[-1] === "&") {
    queryString = queryString.slice(0, -1);
  }

  //fetching data from the controllers based on the query string
  if (!queryString) {
    axios.get("/task_manager/api/tasks/").then(function (res) {
      app.vue.tasks = res.data.tasks;
      app.vue.users = res.data.users;
      app.vue.current_user = res.data.user;
      // Iterate over tasks and fetch comments for each task
      app.vue.tasks.forEach((task) => {
        app.vue.get_comments(task.id);
      });
      app.vue.post_manager(res.data.user.id, "");
      axios
        .get(`/task_manager/api/managers/${res.data.user.id}`)
        .then(function (res) {
          app.vue.manager = res.data.manager.manager;
          app.vue.managed = res.data.managed;
        });
    });
  } else {
    axios.get(`/task_manager/api/tasks?${queryString}`).then(function (res) {
      //Storing the tasks, users, and current users
      app.vue.tasks = res.data.tasks;
      app.vue.users = res.data.users;
      app.vue.current_user = res.data.user;
      // Iterate over tasks and fetch comments for each task
      app.vue.tasks.forEach((task) => {
        app.vue.get_comments(task.id);
      });
      app.vue.post_manager(res.data.user.id, "");
      axios
        .get(`/task_manager/api/managers/${res.data.user.id}`)
        .then(function (res) {
          app.vue.manager = res.data.manager.manager;
          app.vue.managed = res.data.managed;
        });
    });
  }
};

app.vue = Vue.createApp(app.config).mount("#app");
app.load_data();
