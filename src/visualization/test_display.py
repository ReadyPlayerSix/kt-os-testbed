import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("K(t) Framework Test Window")
        self.setGeometry(100, 100, 400, 200)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add a label
        label = QLabel("K(t) Framework GUI Test")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # Add a test button
        button = QPushButton("Test System Integration")
        button.clicked.connect(self.on_button_click)
        layout.addWidget(button)

        self.status_label = QLabel("System status: Ready")
        layout.addWidget(self.status_label)

    def on_button_click(self):
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            status = f"CPU: {cpu_percent}% | Memory: {mem.percent}%"
            self.status_label.setText(f"System status: {status}")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()