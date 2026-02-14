```python
import tkinter as tk
from tkinter import messagebox

class TodoListUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Todo List Application")
        
        self.tasks = []
        
        self.frame = tk.Frame(root)
        self.frame.pack(pady=10)
        
        self.task_listbox = tk.Listbox(self.frame, width=50, height=10, selectmode=tk.SINGLE)
        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        
        self.scrollbar = tk.Scrollbar(self.frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        self.task_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.task_listbox.yview)
        
        self.entry = tk.Entry(root, width=54)
        self.entry.pack(pady=10)
        
        self.add_task_button = tk.Button(root, text="Add Task", command=self.add_task)
        self.add_task_button.pack(pady=5)
        
        self.delete_task_button = tk.Button(root, text="Delete Task", command=self.delete_task)
        self.delete_task_button.pack(pady=5)
        
        self.complete_task_button = tk.Button(root, text="Complete Task", command=self.complete_task)
        self.complete_task_button.pack(pady=5)
    
    def add_task(self):
        task = self.entry.get()
        if task:
            self.tasks.append(task)
            self.update_task_listbox()
            self.entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", "You must enter a task.")
    
    def delete_task(self):
        try:
            selected_task_index = self.task_listbox.curselection()[0]
            self.tasks.pop(selected_task_index)
            self.update_task_listbox()
        except IndexError:
            messagebox.showwarning("Warning", "You must select a task to delete.")
    
    def complete_task(self):
        try:
            selected_task_index = self.task_listbox.curselection()[0]
            self.tasks[selected_task_index] += " - Completed"
            self.update_task_listbox()
        except IndexError:
            messagebox.showwarning("Warning", "You must select a task to mark as complete.")
    
    def update_task_listbox(self):
        self.task_listbox.delete(0, tk.END)
        for task in self.tasks:
            self.task_listbox.insert(tk.END, task)


if __name__ == "__main__":
    root = tk.Tk()
    app = TodoListUI(root)
    root.mainloop()
```