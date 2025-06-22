import os
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog, QComboBox,
    QMessageBox, QInputDialog, QMenuBar, QMainWindow
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt


class ImageApp(QMainWindow):
    """
    Главное окно приложения для загрузки/съемки изображения и отображения RGB-каналов,
    с дополнительными функциями.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Обработка изображения")
        self.image = None  # Оригинальное изображение (NumPy BGR)

        self.label = QLabel("Изображение не выбрано")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(600, 400)

        self.combo_channel = QComboBox()
        self.combo_channel.addItems(["Все каналы", "Красный", "Зеленый", "Синий"])
        self.combo_channel.currentIndexChanged.connect(self.update_display)

        self.btn_load = QPushButton("Загрузить изображение")
        self.btn_load.clicked.connect(self.load_image)

        self.btn_camera = QPushButton("Сделать фото с веб-камеры")
        self.btn_camera.clicked.connect(self.capture_from_camera)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.combo_channel)
        layout.addWidget(self.btn_load)
        layout.addWidget(self.btn_camera)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._create_menu()

    def _create_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        edit_menu = menu_bar.addMenu("Редактировать")

        resize_action = edit_menu.addAction("Изменить размер изображения")
        resize_action.triggered.connect(self.resize_image)

        brightness_action = edit_menu.addAction("Понизить яркость")
        brightness_action.triggered.connect(self.decrease_brightness)

        circle_action = edit_menu.addAction("Нарисовать круг")
        circle_action.triggered.connect(self.draw_circle)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", "Изображения (*.png *.jpg)"
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".png", ".jpg"]:
            QMessageBox.warning(
                self, "Неподдерживаемый формат", "Формат должен быть PNG или JPG."
            )
            return

        try:
            pil_img = Image.open(file_path).convert("RGB")
            self.image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            self.combo_channel.setCurrentIndex(0)
            self.update_display()
            QMessageBox.information(self, "Успех", f"Загружено: {os.path.basename(file_path)}")
        except UnidentifiedImageError:
            QMessageBox.critical(self, "Ошибка", "Файл повреждён или не является изображением.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки:\n{e}")

    def capture_from_camera(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            QMessageBox.critical(self, "Ошибка", "Камера недоступна.")
            return

        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            QMessageBox.critical(self, "Ошибка", "Ошибка получения изображения.")
            return

        self.image = frame
        self.combo_channel.setCurrentIndex(0)
        self.update_display()
        QMessageBox.information(self, "Успех", "Снимок сделан.")

    def update_display(self):
        if self.image is None:
            self.label.setText("Изображение не выбрано")
            return

        idx = self.combo_channel.currentIndex()

        if idx == 0:
            img_to_show = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        else:
            channel_map = {1: 2, 2: 1, 3: 0}
            ch = channel_map[idx]
            blank = np.zeros_like(self.image)
            blank[:, :, ch] = self.image[:, :, ch]
            img_to_show = cv2.cvtColor(blank, cv2.COLOR_BGR2RGB)

        h, w, ch = img_to_show.shape
        bytes_per_line = ch * w
        qt_img = QImage(img_to_show.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        scaled = pixmap.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)

    def resize_image(self):
        if self.image is None:
            QMessageBox.warning(self, "Нет изображения", "Сначала загрузите изображение.")
            return

        w, ok1 = QInputDialog.getInt(self, "Ширина", "Введите новую ширину:", min=1, max=2000)
        if not ok1:
            return
        h, ok2 = QInputDialog.getInt(self, "Высота", "Введите новую высоту:", min=1, max=2000)
        if not ok2:
            return

        self.image = cv2.resize(self.image, (w, h))
        self.update_display()
        QMessageBox.information(self, "Успех", f"Изображение изменено: {w}x{h}")

    def decrease_brightness(self):
        if self.image is None:
            QMessageBox.warning(self, "Нет изображения", "Сначала загрузите изображение.")
            return

        value, ok = QInputDialog.getInt(self, "Уменьшить яркость", "Введите значение (0–255):", min=0, max=255)
        if not ok:
            return

        self.image = np.clip(self.image - value, 0, 255).astype(np.uint8)
        self.update_display()
        QMessageBox.information(self, "Успех", f"Яркость уменьшена на {value}.")

    def draw_circle(self):
        if self.image is None:
            QMessageBox.warning(self, "Нет изображения", "Сначала загрузите изображение.")
            return

        x, ok1 = QInputDialog.getInt(self, "Координата X", "Введите X центра круга:", min=0, max=self.image.shape[1])
        if not ok1:
            return
        y, ok2 = QInputDialog.getInt(self, "Координата Y", "Введите Y центра круга:", min=0, max=self.image.shape[0])
        if not ok2:
            return
        r, ok3 = QInputDialog.getInt(self, "Радиус", "Введите радиус круга:", min=1, max=1000)
        if not ok3:
            return

        self.image = self.image.copy()
        cv2.circle(self.image, (x, y), r, (0, 0, 255), thickness=2)
        self.update_display()
        QMessageBox.information(self, "Успех", "Круг нарисован.")
