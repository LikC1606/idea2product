from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog
)
from PyQt5.QtGui import QPixmap
from src.ai.content_generation import generate_youth_suggestions

class SuggestionsUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Youth-Oriented Product Suggestions")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Image upload section
        self.image_label = QLabel("Upload Product Image:")
        self.image_preview = QLabel("No image selected")
        self.image_preview.setFixedSize(300, 300)
        self.image_preview.setStyleSheet("border: 1px solid #ccc;")
        self.upload_button = QPushButton("Upload Image")
        self.upload_button.clicked.connect(self.upload_image)

        # Text input section
        self.text_label = QLabel("Enter Product Description:")
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your product description here...")

        # Generate suggestions button
        self.generate_button = QPushButton("Generate Suggestions")
        self.generate_button.clicked.connect(self.generate_suggestions)

        # Suggestions output area
        self.output_label = QLabel("Generated Suggestions:")
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)

        # Adding widgets to layout
        layout.addWidget(self.image_label)
        layout.addWidget(self.image_preview)
        layout.addWidget(self.upload_button)
        layout.addWidget(self.text_label)
        layout.addWidget(self.text_input)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_area)

        self.setLayout(layout)

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select an Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            pixmap = QPixmap(file_path).scaled(300, 300, aspectRatioMode=False)
            self.image_preview.setPixmap(pixmap)
            self.image_preview.setText(file_path)
            self.image_file_path = file_path

    def generate_suggestions(self):
        description = self.text_input.text()
        image_path = getattr(self, "image_file_path", None)

        if not description or not image_path:
            self.output_area.setText("Please upload an image and provide a description.")
            return

        suggestions = generate_youth_suggestions(image_path, description)
        self.output_area.setText("\n".join(suggestions))


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SuggestionsUI()
    window.show()
    sys.exit(app.exec_())