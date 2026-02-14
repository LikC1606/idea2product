import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QLineEdit, QLabel, QMessageBox

class TaskOrganizationUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Task Organization')
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()

        self.taskInput = QLineEdit(self)
        self.taskInput.setPlaceholderText("Enter new task")
        layout.addWidget(self.taskInput)
        
        addTaskBtn = QPushButton('Add Task', self)
        addTaskBtn.clicked.connect(self.addTask)
        layout.addWidget(addTaskBtn)

        self.taskList = QListWidget(self)
        layout.addWidget(self.taskList)

        self.setLayout(layout)

    def addTask(self):
        task = self.taskInput.text().strip()
        if task:
            self.taskList.addItem(task)
            self.taskInput.clear()
        else:
            QMessageBox.warning(self, 'Input Error', 'Task cannot be empty.')

def main():
    app = QApplication(sys.argv)
    window = TaskOrganizationUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()