from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QListWidget, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt
import sys

class TaskManagementUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Simple Todo List App')
        self.setGeometry(100, 100, 400, 500)

        # Main layout
        main_layout = QVBoxLayout()

        # Header
        header_label = QLabel('Task Management')
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(header_label)

        # Task input layout
        input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText('Enter a new task...')
        self.add_task_button = QPushButton('Add Task')
        self.add_task_button.clicked.connect(self.add_task)
        input_layout.addWidget(self.task_input)
        input_layout.addWidget(self.add_task_button)
        main_layout.addLayout(input_layout)

        # Task list
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("font-size: 14px;")
        main_layout.addWidget(self.task_list)

        # Task management buttons
        button_layout = QHBoxLayout()
        self.delete_task_button = QPushButton('Delete Task')
        self.delete_task_button.clicked.connect(self.delete_task)
        self.edit_task_button = QPushButton('Edit Task')
        self.edit_task_button.clicked.connect(self.edit_task)
        self.clear_tasks_button = QPushButton('Clear All')
        self.clear_tasks_button.clicked.connect(self.clear_tasks)
        button_layout.addWidget(self.delete_task_button)
        button_layout.addWidget(self.edit_task_button)
        button_layout.addWidget(self.clear_tasks_button)
        main_layout.addLayout(button_layout)

        # Set main layout
        self.setLayout(main_layout)

    def add_task(self):
        task = self.task_input.text().strip()
        if not task:
            QMessageBox.warning(self, 'Warning', 'Task cannot be empty!')
            return
        self.task_list.addItem(task)
        self.task_input.clear()

    def delete_task(self):
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Warning', 'Please select a task to delete!')
            return
        for item in selected_items:
            self.task_list.takeItem(self.task_list.row(item))

    def edit_task(self):
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Warning', 'Please select a task to edit!')
            return
        current_task = selected_items[0].text()
        new_task, ok = QInputDialog.getText(self, 'Edit Task', 'Edit your task:', QLineEdit.Normal, current_task)
        if ok and new_task.strip():
            selected_items[0].setText(new_task.strip())

    def clear_tasks(self):
        confirm = QMessageBox.question(self, 'Clear All Tasks', 
                                       'Are you sure you want to delete all tasks?',
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.task_list.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TaskManagementUI()
    window.show()
    sys.exit(app.exec_())