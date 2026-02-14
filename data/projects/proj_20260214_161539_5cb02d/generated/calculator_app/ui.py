import tkinter as tk

class CalculatorUI:
    def __init__(self, master):
        self.master = master
        master.title("Simple Calculator")

        # Entry widget to display the calculations
        self.entry = tk.Entry(master, width=16, font=("Arial", 24), borderwidth=2, relief="solid")
        self.entry.grid(row=0, column=0, columnspan=4)
        
        # Buttons for the calculator
        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('=', 4, 2), ('+', 4, 3),
        ]

        for (text, row, col) in buttons:
            self.create_button(text, row, col)

    def create_button(self, text, row, col):
        button = tk.Button(self.master, text=text, width=5, height=2, font=("Arial", 18),
                           command=lambda: self.on_button_click(text))
        button.grid(row=row, column=col, sticky="nsew")

    def on_button_click(self, char):
        if char == "=":
            try:
                expression = self.entry.get()
                result = eval(expression)
                self.entry.delete(0, tk.END)
                self.entry.insert(tk.END, str(result))
            except Exception as e:
                self.entry.delete(0, tk.END)
                self.entry.insert(tk.END, "Error")
        else:
            current_text = self.entry.get()
            new_text = current_text + str(char)
            self.entry.delete(0, tk.END)
            self.entry.insert(tk.END, new_text)

if __name__ == "__main__":
    root = tk.Tk()
    calculator_ui = CalculatorUI(root)
    root.mainloop()