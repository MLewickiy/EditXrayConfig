import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QScrollArea, QFrame
)


class FullXrayEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xray Full Config Editor")
        self.config_path = None
        self.config_data = None
        self.inputs = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Файл конфигурации
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл не выбран")
        select_button = QPushButton("Выбрать config.json")
        select_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(select_button)
        layout.addLayout(file_layout)

        # Scroll для полей
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

        # Кнопка сохранить
        save_btn = QPushButton("Сохранить изменения")
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите config.json", "", "JSON Files (*.json)")
        if path:
            self.config_path = Path(path)
            self.file_label.setText(str(self.config_path))
            self.load_config()

    def add_field(self, label_text, value, key_path):
        """Создаёт QLineEdit для редактирования значения"""
        frame = QFrame()
        layout = QHBoxLayout()
        frame.setLayout(layout)
        label = QLabel(label_text)
        input_field = QLineEdit(str(value))
        layout.addWidget(label)
        layout.addWidget(input_field)
        self.scroll_layout.addWidget(frame)
        # Используем кортеж как ключ
        self.inputs[tuple(key_path)] = input_field

    def load_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config_data = json.load(f)

            # Очистка старых полей
            for i in reversed(range(self.scroll_layout.count())):
                self.scroll_layout.itemAt(i).widget().setParent(None)
            self.inputs.clear()

            # --- Inbounds ---
            inbound = self.config_data.get("inbounds", [{}])[0]
            self.add_field("Inbound Port", inbound.get("port", ""), ["inbounds", 0, "port"])
            self.add_field("Inbound Listen", inbound.get("listen", ""), ["inbounds", 0, "listen"])
            self.add_field("Inbound Protocol", inbound.get("protocol", ""), ["inbounds", 0, "protocol"])
            self.add_field("Inbound UDP", inbound.get("settings", {}).get("udp", ""), ["inbounds", 0, "settings", "udp"])

            # --- Outbounds ---
            outbound = self.config_data.get("outbounds", [{}])[0]
            self.add_field("Outbound Protocol", outbound.get("protocol", ""), ["outbounds", 0, "protocol"])

            vnext = outbound.get("settings", {}).get("vnext", [{}])[0]
            self.add_field("VNext Address", vnext.get("address", ""), ["outbounds", 0, "settings", "vnext", 0, "address"])
            self.add_field("VNext Port", vnext.get("port", ""), ["outbounds", 0, "settings", "vnext", 0, "port"])

            user = vnext.get("users", [{}])[0]
            self.add_field("User ID", user.get("id", ""), ["outbounds", 0, "settings", "vnext", 0, "users", 0, "id"])
            self.add_field("User Flow", user.get("flow", ""), ["outbounds", 0, "settings", "vnext", 0, "users", 0, "flow"])
            self.add_field("User Encryption", user.get("encryption", ""), ["outbounds", 0, "settings", "vnext", 0, "users", 0, "encryption"])

            stream = outbound.get("streamSettings", {})
            self.add_field("Network", stream.get("network", ""), ["outbounds", 0, "streamSettings", "network"])
            self.add_field("Security", stream.get("security", ""), ["outbounds", 0, "streamSettings", "security"])

            reality = stream.get("realitySettings", {})
            self.add_field("PublicKey", reality.get("publicKey", ""), ["outbounds", 0, "streamSettings", "realitySettings", "publicKey"])
            self.add_field("ShortID", reality.get("shortId", ""), ["outbounds", 0, "streamSettings", "realitySettings", "shortId"])
            self.add_field("ServerName", reality.get("serverName", ""), ["outbounds", 0, "streamSettings", "realitySettings", "serverName"])
            self.add_field("Fingerprint", reality.get("fingerprint", ""), ["outbounds", 0, "streamSettings", "realitySettings", "fingerprint"])
            self.add_field("SPX", reality.get("spx", ""), ["outbounds", 0, "streamSettings", "realitySettings", "spx"])

            QMessageBox.information(self, "Готово", "Все поля загружены для редактирования!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить config.json:\n{e}")

    def set_nested(self, data, key_path, value):
        """Обновление значения в nested dict/list по пути с учётом типов"""
        d = data
        for key in key_path[:-1]:
            d = d[key]
        current_value = d[key_path[-1]]

        if isinstance(current_value, bool):
            # Любой вариант: True, true, 1, yes → True
            d[key_path[-1]] = str(value).strip().lower() in ["true", "1", "yes"]
        elif isinstance(current_value, int):
            # Убираем лишние пробелы
            try:
                d[key_path[-1]] = int(str(value).strip())
            except ValueError:
                QMessageBox.warning(None, "Ошибка", f"Поле {key_path[-1]} должно быть числом")
                return
        else:
            d[key_path[-1]] = value

    def save_config(self):
        try:
            for key_path, widget in self.inputs.items():
                self.set_nested(self.config_data, list(key_path), widget.text())
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4)
            QMessageBox.information(self, "Готово", "Изменения сохранены!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = FullXrayEditor()
    editor.show()
    sys.exit(app.exec())
