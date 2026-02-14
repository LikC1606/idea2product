from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit
)
from PyQt5.QtCore import Qt
from src.backend.text_input_backend import process_user_input


class TextInputUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        
        # Title Label
        self.title_label = QLabel("Product Description Generator")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Image Upload Section
        self.image_upload_label = QLabel("Upload Product Image:")
        self.image_upload_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.image_upload_label)
        
        self.upload_button = QPushButton("Upload Image")
        self.upload_button.setStyleSheet("font-size: 14px; padding: 5px;")
        self.upload_button.clicked.connect(self.upload_image)
        layout.addWidget(self.upload_button)
        
        self.uploaded_image_path = QLabel("")
        self.uploaded_image_path.setStyleSheet("font-size: 12px; color: gray;")
        layout.addWidget(self.uploaded_image_path)
        
        # Text Input Section
        self.input_label = QLabel("Enter Product Description:")
        self.input_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.input_label)
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type product description here...")
        self.text_input.setStyleSheet("font-size: 14px; padding: 5px;")
        layout.addWidget(self.text_input)
        
        # Generate Button
        self.generate_button = QPushButton("Generate Content")
        self.generate_button.setStyleSheet(
            "font-size: 14px; padding: 10px; background-color: #4CAF50; color: white; border-radius: 5px;"
        )
        self.generate_button.clicked.connect(self.generate_content)
        layout.addWidget(self.generate_button)
        
        # Output Section
        self.output_label = QLabel("Generated Content:")
        self.output_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        layout.addWidget(self.output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("font-size: 14px; background-color: #f9f9f9; padding: 5px;")
        layout.addWidget(self.output_text)
        
        # Set layout
        self.setLayout(layout)
        self.setWindowTitle("Product Description Generator")
    
    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.uploaded_image_path.setText(f"Selected: {file_path}")
        else:
            self.uploaded_image_path.setText("No image selected.")
    
    def generate_content(self):
        image_path = self.uploaded_image_path.text().replace("Selected: ", "").strip()
        user_input = self.text_input.text().strip()
        
        if not image_path or image_path == "No image selected.":
            self.output_text.setText("Error: Please upload an image.")
            return
        
        if not user_input:
            self.output_text.setText("Error: Please enter a product description.")
            return
        
        # Call backend function
        try:
            generated_content = process_user_input(image_path, user_input)
            self.output_text.setText(generated_content)
        except Exception as e:
            self.output_text.setText(f"Error: {str(e)}")