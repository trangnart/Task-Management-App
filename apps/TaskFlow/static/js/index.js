const { createApp, reactive, onMounted, watch } = Vue;

const TaskManager = {
  template: `
    <div>
      <div class="task-container">
        <div class="task-form">
          <h4>Create a Task</h4>
          <input v-model="state.newTask.title" id="task-title" placeholder="Task Title">
          <textarea v-model="state.newTask.description" id="task-description" placeholder="Task Description"></textarea>
          <p> Status </p>
          <select v-model="state.newTask.status" id="task-status">
          <option value="pending">Pending</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="rejected">Rejected</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
        <p> Priority </p>
        <select v-model="state.newTask.priority" id="task-priority">
        <option value="Low">Low</option>
        <option value="Medium">Medium</option>
        <option value="High">High</option>
      </select>

          <p> Deadline </p>
          <input type="datetime-local" v-model="state.newTask.deadline" id="task-deadline" placeholder="Deadline">
          <p> Assigned To: </p>
          <select v-model="state.newTask.assigned_to" id="task-assigned-to">
            
           
            <option :value="null">None</option> 
            <option v-for="user in state.users" :value="user.id">{{ user.email }}</option>
          </select>
          <button @click="submitTask">Add Task</button>
        </div>
        <div class="change-manager">
          <h4>Change Manager</h4>
          <select v-model="state.newManagerId">
            <option :value="null">Select Manager</option>
            <option v-for="user in state.users" :value="user.id">{{ user.email }}</option>
          </select>
          <button @click="changeManager">Change</button>
        </div>
      </div>
      <div class="filters">
        <h4>Filters</h4>
        <div>
     
          <select v-model="state.filters.status" @change="fetchTasks">
          <option value="">Status</option>
          <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="rejected">Rejected</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
        <div>
          <label>Date Created:</label>
          <input type="date" v-model="state.filters.date_created" @change="fetchTasks">
        </div>
   

        <div>
          <label>Created by Me:</label>
          <input type="checkbox" v-model="state.filters.created_by_me" @change="fetchTasks">
        </div>
        <div>
          <label>Assigned to Me:</label>
          <input type="checkbox" v-model="state.filters.assigned_to_me" @change="fetchTasks">
        </div>
      

      </div>
      <table id="taskTable">
        <thead>
          <tr>
            <th>Task</th>
            <th>Description</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Deadline</th>
            <th>Owner</th>
            <th>Assigned To</th>
            <th>Comments</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in state.tasks" :key="task.id">
            <td>{{ task.title }}</td>
            <td>{{ task.description }}</td>
          
            <td>{{ task.priority }}</td>
            <td>{{ task.status }}</td>
            <td>{{ task.deadline }}</td>
            <td>{{ getUserById(task.created_by).email }}</td>
            <td>{{ getUserById(task.assigned_to).email }}</td>
            <td>
              <div v-if="task.comment_text">
                <p v-for="comment in task.comment_text.split('\\n')" :key="comment">{{ comment }}</p>
              </div>
              <textarea v-model="state.newComment[task.id]" placeholder="Add a comment"></textarea>
              <button @click="addComment(task.id)">Add Comment</button>
            </td>
            <td>
              <button @click="editTask(task)">Edit</button>
              <button @click="deleteTask(task.id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="state.showSuccessPopup" class="popup-modal">
        <div class="popup-content">
          <span class="close" @click="state.showSuccessPopup = false">&times;</span>
          <p>{{ state.success }}</p>
        </div>
      </div>
      <div v-if="state.showErrorPopup" class="popup-modal">
        <div class="popup-content">
          <span class="close" @click="state.showErrorPopup = false">&times;</span>
          <p>{{ state.error }}</p>
        </div>
      </div>
      <div v-if="state.showEditPopup" class="popup-modal">
        <div class="popup-content">
          <span class="close" @click="state.showEditPopup = false">&times;</span>
          <h2>Edit Task</h2>
          <p>Task title</p>
          <input v-model="state.editTask.title" id="edit-task-title" placeholder="Task Title">
          <p>Task Description</p>
          <textarea v-model="state.editTask.description" id="edit-task-description" placeholder="Task Description"></textarea>
          <p>Status</p>
          <select v-model="state.editTask.status" id="edit-task-status">
            <option value="pending">Pending</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="rejected">Rejected</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
          <p>Priority</p>
          <select v-model="state.editTask.priority" id="edit-task-priority">
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
          <p>Deadline</p>
          <input type="datetime-local" v-model="state.editTask.deadline" id="edit-task-deadline" placeholder="Deadline">
          <p> Assigned To:</p>
          <select v-model="state.editTask.assigned_to" id="edit-task-assigned-to">
            <option :value="null">None</option>
            <option v-for="user in state.users" :value="user.id">{{ user.email }}</option>
          </select>
          <button @click="updateTask">Update Task</button>
          <button @click="cancelEdit">Cancel</button>
        </div>
      </div>
    </div>
  `,
  setup() {
    const state = reactive({
      newTask: {
        title: '',
        description: '',
        status: 'pending',
        priority: 'Low',
        deadline: '',
        assigned_to: null
      },
      editTask: {
        id: null,
        title: '',
        description: '',
        status: 'pending',
        priority: 'Low',
        deadline: '',
        assigned_to: null
      },
      newManagerId: null,
      tasks: [],
      users: [],
      managedUsers: [],
      newComment: {},
      error: '',
      success: '',
      showSuccessPopup: false,
      showErrorPopup: false,
      showEditPopup: false,
      filters: {
        status: '',
        date_created: '',
        deadline: '',
        created_by_me: false,
        assigned_to_me: false,
        created_by_user: '',
        assigned_to_user: '',
        created_by_managed_user: null,
        assigned_to_managed_user: null
      }
    });

    const fetchTasks = () => {
      const url = '/TaskFlow/api/tasks';
      const params = new URLSearchParams();
    
      console.log("fetch task",state.filters);
      console.log("Selected status filter:", state.filters.status);
      console.log("Selected deadline filter:", state.filters.deadline);
    
      if (state.filters.status) params.append('status', state.filters.status);
      if (state.filters.date_created) params.append('date_created', state.filters.date_created);
      console.log('hiii')
        
      // Convert the deadline to ISO string without milliseconds
      if (state.filters.deadline) {
        console.log('date conversion')
        const deadline = new Date(state.filters.deadline).toISOString().split('.')[0] + 'Z';
        params.append('deadline', deadline);
      }
      console.log("fetch task",state.filters); 
      console.log("created by_me",state.filters.created_by_me)
      if (state.filters.created_by_me) params.append('created_by', state.filters.created_by); 
      // Add other filter parameters
      if (state.filters.assigned_to_me) params.append('assigned_to', state.filters.assigned_to); 
      
      
      console.log("user",state.filters.created_by_user)
      if (state.filters.created_by_user) {
        const user = state.users.find(u => u.name === state.filters.created_by_user);
        if (user) {
          console.log('append')
          params.append('created_by', user.id);
        } else {
          console.log('dont append') 
          // Handle case where user is not found
        }
      }




      fetch(`${url}?${params.toString()}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      .then(response => response.json())
      .then(data => {
        state.tasks = data.tasks;
      })
      .catch(error => {
        state.error = 'Error fetching tasks: ' + error.message;
        state.showErrorPopup = true;
      });
    };
    const fetchUsers = () => {
      fetch('/TaskFlow/api/users', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      .then(response => response.json())
      .then(data => {
        state.users = data.users;
      })
      .catch(error => {
        console.error('Error fetching users:', error.message);
      });
    };
    const toggleStatusDropdown = () => {
      state.showStatusDropdown = !state.showStatusDropdown;
    };
    
    const submitTask = () => {
      console.log('submit task');
      console.log('newTask:', state.newTask); // Add this line to log the newTask object
      
      if (!state.newTask.title || !state.newTask.description) {
        state.error = 'Title and description are required.';
        state.showErrorPopup = true;
        return;
      }
    
      fetch('/TaskFlow/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state.newTask)
      }).then(response => {
        if (!response.ok) throw new Error('Failed to add task');
        return response.json();
      }).then(() => {
        state.newTask = {
          title: '',
          description: '',
          status: 'pending',
          priority: 'Low',
          deadline: '',
          assigned_to: null
        };
        fetchTasks();
        state.success = 'Task added successfully!';
        state.showSuccessPopup = true;
      }).catch(error => {
        state.error = 'Error submitting task: ' + error.message;
        state.showErrorPopup = true;
      });
    };

    const addComment = (taskId) => {
      const commentText = state.newComment[taskId];
      if (!commentText) {
        state.error = 'Comment text is required.';
        state.showErrorPopup = true;
        return;
      }

      fetch(`/TaskFlow/api/tasks/${taskId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comment_text: commentText })
      }).then(response => {
        if (!response.ok) throw new Error('Failed to add comment');
        return response.json();
      }).then(() => {
        state.newComment[taskId] = '';
        fetchTasks();
        state.success = 'Comment added successfully!';
        state.showSuccessPopup = true;
      }).catch(error => {
        state.error = 'Error adding comment: ' + error.message;
        state.showErrorPopup = true;
      });
    };

    const editTask = (task) => {
      state.editTask = { ...task };
      state.editTask.deadline = task.deadline ? task.deadline.replace(' ', 'T') : '';
      state.showEditPopup = true;  // Show the edit popup
    };
      const updateTask = () => {
        if (!state.editTask.id) {
          state.error = 'No task selected for editing.';
          state.showErrorPopup = true;
          return;
        }
      
        fetch(`/TaskFlow/api/tasks/${state.editTask.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(state.editTask)
        }).then(response => {
          if (!response.ok) {
            if (response.status === 403) {
              throw new Error('You do not have permission to edit this task');
            } else {
              throw new Error('Failed to update task');
            }
          }
          return response.json();
        }).then(() => {
          state.editTask = {
            id: null,
            title: '',
            description: '',
            status: 'pending',
            priority: 'Low',
            deadline: '',
            assigned_to: null
          };
          fetchTasks();
          state.success = 'Task updated successfully!';
          state.showSuccessPopup = true;
          state.showEditPopup = false;  // Hide the edit popup
        }).catch(error => {
          state.error = 'Error updating task: ' + error.message;
          state.showErrorPopup = true;
        });
      };
      
      const cancelEdit = () => {
        state.editTask = {
          id: null,
          title: '',
          description: '',
          status: 'pending',
          priority: 'Low',
          deadline: '',
          assigned_to: null
        };
        state.showEditPopup = false;  // Hide the edit popup
      };
      
      const deleteTask = (taskId) => {
        fetch(`/TaskFlow/api/tasks/${taskId}`, {
          method: 'DELETE'
        }).then(response => {
          if (!response.ok) throw new Error('Failed to delete task');
          fetchTasks();
          state.success = 'Task deleted successfully!';
          state.showSuccessPopup = true;
        }).catch(error => {
          state.error = 'Error deleting task: ' + error.message;
          state.showErrorPopup = true;
        });
      };
      
      const changeManager = () => {
        if (!state.newManagerId) {
          state.error = 'Please select a manager.';
          state.showErrorPopup = true;
          return;
        }
      
        fetch('/TaskFlow/api/update_manager', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ manager_id: state.newManagerId })
        }).then(response => {
          if (!response.ok) throw new Error('Failed to update manager');
          return response.json();
        }).then(() => {
          state.newManagerId = null;
          state.success = 'Manager updated successfully!';
          state.showSuccessPopup = true;
        }).catch(error => {
          state.error = 'Error updating manager: ' + error.message;
          state.showErrorPopup = true;
        });
      };
      
      const getUserById = (id) => {
        return state.users.find(user => user.id === id) || {};
      };

      onMounted(() => {
        fetchTasks();
        fetchUsers();
      });
      
      return { state,fetchTasks, submitTask, addComment, editTask, updateTask, cancelEdit, deleteTask, changeManager, getUserById,toggleStatusDropdown };
    }
  };
  
  createApp(TaskManager).mount('#app');