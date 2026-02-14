document.addEventListener("DOMContentLoaded", function() {
    // Task List
    const taskList = document.getElementById('task-list');

    // Task Input
    const taskInput = document.getElementById('task-input');

    // Add Task Button
    const addTaskButton = document.getElementById('add-task');

    // Event Listener for Adding Tasks
    addTaskButton.addEventListener('click', function() {
        const taskText = taskInput.value.trim();
        if (taskText !== "") {
            addTask(taskText);
            taskInput.value = '';
        }
    });

    // Function to Add Task
    function addTask(taskText) {
        const taskItem = document.createElement('li');
        taskItem.className = 'task-item';

        // Task Content
        const taskContent = document.createElement('span');
        taskContent.className = 'task-content';
        taskContent.textContent = taskText;
        taskItem.appendChild(taskContent);

        // Task Priority
        const prioritySelect = document.createElement('select');
        prioritySelect.className = 'task-priority';
        ['Low', 'Medium', 'High'].forEach(priority => {
            const option = document.createElement('option');
            option.value = priority;
            option.textContent = priority;
            prioritySelect.appendChild(option);
        });
        taskItem.appendChild(prioritySelect);

        // Completion Checkbox
        const completionCheckbox = document.createElement('input');
        completionCheckbox.type = 'checkbox';
        completionCheckbox.className = 'task-completion';
        completionCheckbox.addEventListener('change', function() {
            taskContent.classList.toggle('completed', completionCheckbox.checked);
        });
        taskItem.appendChild(completionCheckbox);

        // Edit Button
        const editButton = document.createElement('button');
        editButton.className = 'edit-task';
        editButton.textContent = 'Edit';
        editButton.addEventListener('click', function() {
            editTask(taskItem);
        });
        taskItem.appendChild(editButton);

        // Delete Button
        const deleteButton = document.createElement('button');
        deleteButton.className = 'delete-task';
        deleteButton.textContent = 'Delete';
        deleteButton.addEventListener('click', function() {
            deleteTask(taskItem);
        });
        taskItem.appendChild(deleteButton);

        taskList.appendChild(taskItem);
    }

    // Function to Edit Task
    function editTask(taskItem) {
        const taskContent = taskItem.querySelector('.task-content');
        const newTaskText = prompt("Edit Task:", taskContent.textContent);
        if (newTaskText !== null) {
            taskContent.textContent = newTaskText.trim();
        }
    }

    // Function to Delete Task
    function deleteTask(taskItem) {
        taskList.removeChild(taskItem);
    }
});