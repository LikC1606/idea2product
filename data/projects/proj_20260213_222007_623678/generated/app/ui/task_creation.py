import tkinter as tk
from tkinter import messagebox

class TaskCreationUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Creation")
        
        self.create_widgets()

    def create_widgets(self):
        # Task Name
        self.task_name_label = tk.Label(self.root, text="Task Name:")
        self.task_name_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.task_name_entry = tk.Entry(self.root, width=50)
        self.task_name_entry.grid(row=0, column=1, padx=10, pady=10)

        # Task Description
        self.task_desc_label = tk.Label(self.root, text="Task Description:")
        self.task_desc_label.grid(row=1, column=0, padx=10, pady=10)
        
        self.task_desc_entry = tk.Text(self.root, width=50, height=5)
        self.task_desc_entry.grid(row=1, column=1, padx=10, pady=10)

        # Due Date
        self.due_date_label = tk.Label(self.root, text="Due Date (YYYY-MM-DD):")
        self.due_date_label.grid(row=2, column=0, padx=10, pady=10)
        
        self.due_date_entry = tk.Entry(self.root, width=50)
        self.due_date_entry.grid(row=2, column=1, padx=10, pady=10)

        # Create Task Button
        self.create_task_button = tk.Button(self.root, text="Create Task", command=self.create_task)
        self.create_task_button.grid(row=3, column=1, pady=20)

    def create_task(self):
        task_name = self.task_name_entry.get()
        task_desc = self.task_desc_entry.get("1.0", tk.END).strip()
        due_date = self.due_date_entry.get()

        if not task_name or not due_date:
            messagebox.showwarning("Input Error", "Task name and due date are required!")
            return

        # Here you would add code to save the task to a database or a file

        messagebox.showinfo("Task Created", f"Task '{task_name}' created successfully!")
        self.clear_entries()

    def clear_entries(self):
        self.task_name_entry.delete(0, tk.END)
        self.task_desc_entry.delete("1.0", tk.END)
        self.due_date_entry.delete(0, tk.END)

def main():
    root = tk.Tk()
    app = TaskCreationUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()