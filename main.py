import sys
import json
import urllib.parse
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt


class FullXrayEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xray Config Editor")
        self.config_path = None
        self.config_data = None
        self.inputs = {}
        self.label_to_key = {}

        self.resize(500, 600)
        self.setMinimumSize(500, 600)

        self.init_ui()
        self.apply_styles()

    # ----------------- UI -----------------
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- Файл конфигурации ---
        file_layout = QHBoxLayout()
        file_layout.setSpacing(10)
        self.file_label = QLabel("Файл не выбран")
        self.file_label.setStyleSheet("font-weight: bold; color: #000000;")
        select_button = QPushButton("Выбрать config.json")
        select_button.clicked.connect(self.select_file)
        select_button.setCursor(Qt.CursorShape.PointingHandCursor)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(select_button)
        main_layout.addLayout(file_layout)

        # --- Кнопка вставки VLESS ---
        paste_button = QPushButton("Вставить из буфера (VLESS)")
        paste_button.clicked.connect(self.paste_vless)
        paste_button.setCursor(Qt.CursorShape.PointingHandCursor)
        main_layout.addWidget(paste_button)

        # --- Scroll area для полей ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

        # --- Кнопка сохранить ---
        save_btn = QPushButton("Сохранить изменения")
        save_btn.clicked.connect(self.save_config)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            "font-weight: bold; font-size: 14px; background-color: #4CAF50; color: white; padding: 8px; border-radius: 6px;"
        )
        main_layout.addWidget(save_btn)

        self.setLayout(main_layout)

    # ----------------- Поля -----------------
    def add_field(self, label_text, value, key_path):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        frame.setLayout(layout)
        label = QLabel(label_text)
        label.setFixedWidth(120)
        label.setStyleSheet("color: #000000; font-weight: bold;")
        input_field = QLineEdit(str(value))
        input_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
                background-color: #ffffff;
                color: #000000;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)
        layout.addWidget(label)
        layout.addWidget(input_field)
        self.scroll_layout.addWidget(frame)
        key_path_tuple = tuple(key_path)
        self.inputs[key_path_tuple] = input_field
        self.label_to_key[label_text] = key_path_tuple

    # ----------------- Загрузка файла -----------------
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

            # --- DNS Servers ---
            dns_servers = self.config_data.get("dns", {}).get("servers", [])
            for i, server in enumerate(dns_servers):
                self.add_field(f"DNS Server {i+1}", server, ["dns", "servers", i])

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

            # --- Диалоговое окно с черным текстом ---
            self.show_message("Готово", "Все поля загружены для редактирования!")

        except Exception as e:
            self.show_message("Ошибка", f"Не удалось загрузить config.json:\n{e}", icon=QMessageBox.Icon.Critical)

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
                self.show_message("Ошибка", f"Поле {key_path[-1]} должно быть числом", icon=QMessageBox.Icon.Warning)
                return
        else:
            d[key_path[-1]] = value

    def save_config(self):
        try:
            for key_path, widget in self.inputs.items():
                self.set_nested(self.config_data, list(key_path), widget.text())
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4)
            self.show_message("Готово", "Изменения сохранены!")
        except Exception as e:
            self.show_message("Ошибка", f"Не удалось сохранить изменения:\n{e}", icon=QMessageBox.Icon.Critical)

    # ----------------- Вставка VLESS -----------------
    def paste_vless(self):
        clipboard = QApplication.clipboard()
        vless_url = clipboard.text().strip()
        if not vless_url.startswith("vless://"):
            self.show_message("Ошибка", "В буфере нет ссылки VLESS", icon=QMessageBox.Icon.Warning)
            return

        try:
            scheme, rest = vless_url.split("://", 1)
            user_host, host_port_and_params = rest.split("@", 1)

            if "?" in host_port_and_params:
                host_port, query_string_hash = host_port_and_params.split("?", 1)
            else:
                host_port, query_string_hash = host_port_and_params, ""

            query_string = query_string_hash.split("#")[0] if "#" in query_string_hash else query_string_hash
            query = urllib.parse.parse_qs(query_string)

            if ":" in host_port:
                host, port = host_port.split(":", 1)
            else:
                host, port = host_port, ""

            mapping = {
                "User ID": user_host,
                "VNext Address": host,
                "VNext Port": port,
                "Network": query.get("type", [None])[0],
                "Security": query.get("security", [None])[0],
                "PublicKey": query.get("pbk", [None])[0],
                "Fingerprint": query.get("fp", [None])[0],
                "ServerName": query.get("sni", [None])[0],
                "ShortID": query.get("sid", [None])[0],
                "SPX": query.get("spx", [None])[0],
            }

            for label, value in mapping.items():
                if value is not None:
                    key_path = self.label_to_key.get(label)
                    if key_path and key_path in self.inputs:
                        self.inputs[key_path].setText(value)

        except Exception as e:
            self.show_message("Ошибка", f"Не удалось разобрать ссылку VLESS:\n{e}", icon=QMessageBox.Icon.Critical)

    # ----------------- Сообщения -----------------
    def show_message(self, title, text, icon=QMessageBox.Icon.Information):
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStyleSheet("QLabel{color: #000000;} QPushButton{min-width: 80px;}")
        msg.exec()

    # ----------------- Стили -----------------
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f2f5;
                font-family: Arial;
                font-size: 12pt;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = FullXrayEditor()
    editor.show()
    sys.exit(app.exec())
