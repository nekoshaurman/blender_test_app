import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt


class MiniBlock(QWidget):
    def __init__(self, number1, number2, info_label, parent=None):
        super().__init__(parent)
        self.number1 = number1
        self.number2 = number2
        self.is_selected = False  # Флаг для отслеживания состояния выделения
        self.info_label = info_label  # Ссылка на QLabel для вывода информации

        # Создаем макет для мини-блока
        layout = QHBoxLayout(self)
        self.setLayout(layout)

        # Отображаем первое число
        self.label = QLabel(str(number1))
        layout.addWidget(self.label)

        # Кнопка удаления блока
        self.delete_button = QPushButton("X")
        self.delete_button.clicked.connect(self.deleteLater)
        layout.addWidget(self.delete_button)

        # Сохраняем второе число в данных виджета
        self.setData("number2", number2)

        # Делаем блок кликабельным
        self.setMouseTracking(True)
        self.setStyleSheet(self.default_style())  # Устанавливаем начальный стиль

    def default_style(self):
        return "border: 1px solid black; padding: 5px; margin: 5px;"

    def selected_style(self):
        return "border: 1px solid blue; background-color: lightblue; padding: 5px; margin: 5px;"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Переключаем состояние выделения
            self.is_selected = not self.is_selected
            if self.is_selected:
                self.setStyleSheet(self.selected_style())  # Применяем стиль выделения
            else:
                self.setStyleSheet(self.default_style())  # Возвращаем обычный стиль

            # Обновляем информацию в Label
            self.info_label.setText(f"Last selected number2: {self.data('number2')}")
            print(f"Clicked on block with number2: {self.data('number2')}")

    def setData(self, key, value):
        self.setProperty(key, value)

    def data(self, key):
        return self.property(key)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Mini Blocks Example")

        # Главный макет
        main_layout = QHBoxLayout(self)  # Используем QHBoxLayout для размещения блоков и информационного окна

        # Грид для размещения мини-блоков
        self.grid_layout = QGridLayout()
        blocks_container = QVBoxLayout()  # Контейнер для блоков
        blocks_container.addLayout(self.grid_layout)

        # Кнопка добавления мини-блоков
        add_button = QPushButton("Add Block")
        add_button.clicked.connect(self.add_block)
        blocks_container.addWidget(add_button)

        # Добавляем контейнер с блоками в главный макет
        main_layout.addLayout(blocks_container)

        # Информационное окно
        self.info_label = QLabel("Last selected number2: None")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("border: 1px solid gray; padding: 10px; min-width: 150px;")
        main_layout.addWidget(self.info_label)

    def add_block(self):
        try:
            # Генерируем два случайных числа
            number1 = random.randint(1, 100)
            number2 = random.randint(101, 200)

            # Создаем новый мини-блок, передавая ссылку на info_label
            block = MiniBlock(number1, number2, self.info_label, self)

            # Находим первую свободную позицию в гриде
            row = self.grid_layout.rowCount()
            self.grid_layout.addWidget(block, row, 0)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add block: {str(e)}")

    def closeEvent(self, event):
        # Показываем сообщение при закрытии приложения
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(600, 400)
    window.show()

    # Запускаем главный цикл приложения
    sys.exit(app.exec_())