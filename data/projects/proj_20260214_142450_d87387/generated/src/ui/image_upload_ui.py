from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit, QHBoxLayout
from PyQt5.QtGui import QPixmap
from src.backend.image_upload_backend import process_image

class ImageUploadUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Main layout
        self.layout = QVBoxLayout()

        # Title label
        self.title_label = QLabel("Product Description Generator")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; text-align: center;")
        self.layout.addWidget(self.title_label)

        # Instruction label
        self.instruction_label = QLabel("Upload an image and add a description to generate youth-oriented product suggestions.")
        self.instruction_label.setStyleSheet("font-size: 14px; color: gray; margin-bottom: 10px;")
        self.layout.addWidget(self.instruction_label)

        # Image upload section
        self.image_preview = QLabel("Image Preview")
        self.image_preview.setStyleSheet("border: 1px solid gray; height: 200px; width: 200px; text-align: center;")
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.image_preview)

        self.upload_button = QPushButton("Upload Image")
        self.upload_button.clicked.connect(self.upload_image)
        self.layout.addWidget(self.upload_button)

        # Text input section
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter product details or description...")
        self.layout.addWidget(self.text_input)

        # Generate button
        self.generate_button = QPushButton("Generate Product Description")
        self.generate_button.clicked.connect(self.generate_description)
        self.layout.addWidget(self.generate_button)

        # Output section
        self.output_label = QLabel("Generated Suggestions:")
        self.output_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 20px;")
        self.layout.addWidget(self.output_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.layout.addWidget(self.output_text)

        # Set main layout
        self.setLayout(self.layout)

    def upload_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select an Image", "", "Images (*.png *.jpg *.jpeg)", options=options)
        if file_path:
            pixmap = QPixmap(file_path)
            self.image_preview.setPixmap(pixmap.scaled(200, 200))
            self.image_path = file_path

    def generate_description(self):
        if hasattr(self, 'image_path'):
            image_data = process_image(self.image_path)
            user_text = self.text_input.toPlainText()
            generated_suggestions = self.generate_youth_oriented_description(image_data, user_text)
            self.output_text.setPlainText(generated_suggestions)
        else:
            self.output_text.setPlainText("Please upload an image first.")

    def generate_youth_oriented_description(self, image_data, user_text):
        # Placeholder function for backend integration
        # Replace this with actual backend processing
        return f"Generated suggestions based on image data: {image_data} and user text: {user_text}."