import sys
from PyQt5.QtWidgets import QApplication
from image_app.image_app import ImageApp


def main():
    app = QApplication(sys.argv)
    window = ImageApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
