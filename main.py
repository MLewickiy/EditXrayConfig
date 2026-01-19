import sys
import json
import urllib.parse
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtGui import QShortcut, QClipboard
from PyQt6.QtCore import QMimeData


class FullXrayEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xray Full Config Editor")
        self.config_path = None
        self.config_data = None
        self.inputs = {}
        self.label_to_key = {}

        # --- Настройка начального размера окна ---
        self.resize(200, 500)          # стартовый размер (ширина 900, высота 600)
        self.setMinimumSize(400, 500)  # минимальный размер

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

        # Кнопка вставки VLESS
        paste_button = QPushButton("Вставить из буфера (VLESS)")
        paste_button.clicked.connect(self.paste_vless)
        layout.addWidget(paste_button)

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

    # ----------------- GUI поля -----------------
    def add_field(self, label_text, value, key_path):
        frame = QFrame()
        layout = QHBoxLayout()
        frame.setLayout(layout)
        label = QLabel(label_text)
        input_field = QLineEdit(str(value))
        layout.addWidget(label)
        layout.addWidget(input_field)
        self.scroll_layout.addWidget(frame)
        key_path_tuple = tuple(key_path)
        self.inputs[key_path_tuple] = input_field
        self.label_to_key[label_text] = key_path_tuple

    # ----------------- Загрузка -----------------
    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите config.json", "", "JSON Files (*.json)")
        if path:
            self.config_path = Path(path)
            self.file_label.setText(str(self.config_path))
            self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config_data = json.load(f)

            # Очистка старых полей
            for i in reversed(range(self.scroll_layout.count())):
                self.scroll_layout.itemAt(i).widget().setParent(None)
            self.inputs.clear()
            self.label_to_key.clear()

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

            # --- Увеличение окна вниз после загрузки файла ---
            self.resize(self.width(), self.height() + 150)  # увеличиваем высоту на 150px

            QMessageBox.information(self, "Готово", "Все поля загружены для редактирования!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить config.json:\n{e}")

    # ----------------- Сохранение -----------------
    def set_nested(self, data, key_path, value):
        d = data
        for key in key_path[:-1]:
            d = d[key]
        current_value = d[key_path[-1]]
        if isinstance(current_value, bool):
            d[key_path[-1]] = str(value).strip().lower() in ["true", "1", "yes"]
        elif isinstance(current_value, int):
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

    # ----------------- Вставка VLESS -----------------
    def paste_vless(self):
        clipboard = QApplication.clipboard()
        vless_url = clipboard.text().strip()
        if not vless_url.startswith("vless://"):
            QMessageBox.warning(self, "Ошибка", "В буфере нет ссылки VLESS")
            return

        try:
            # Разбираем URL
            scheme, rest = vless_url.split("://", 1)
            user_host, params_hash = rest.split("@", 1)
            user_id = user_host
            host_port, params = params_hash.split("?", 1)
            if "#" in params:
                query_string, name = params.split("#", 1)
            else:
                query_string, name = params, ""

            if ":" in host_port:
                host, port = host_port.split(":", 1)
            else:
                host, port = host_port, ""

            query = urllib.parse.parse_qs(query_string)

            mapping = {
                "User ID": user_id,
                "VNext Address": host,
                "VNext Port": port,
                "Network": query.get("type", ["tcp"])[0],
                "Security": query.get("security", [""])[0],
                "PublicKey": query.get("pbk", [""])[0],
                "Fingerprint": query.get("fp", [""])[0],
                "ServerName": query.get("sni", [""])[0],
                "ShortID": query.get("sid", [""])[0],
                "SPX": query.get("spx", [""])[0],
                "User Flow": "",
                "User Encryption": "none",
                "Outbound Protocol": "vless"
            }

            # Обновляем QLineEdit по ключам
            for label, value in mapping.items():
                key_path = self.label_to_key.get(label)
                if key_path and key_path in self.inputs:
                    self.inputs[key_path].setText(value)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось разобрать ссылку VLESS:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = FullXrayEditor()
    editor.show()
    sys.exit(app.exec())
