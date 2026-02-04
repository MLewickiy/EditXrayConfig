import sys
import json
import re
import urllib.parse
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QScrollArea, QFrame,
    QCheckBox
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
        self.checkboxes = {}

        self.resize(600, 700)
        self.setMinimumSize(600, 700)

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

        new_button = QPushButton("Новый config")
        new_button.clicked.connect(self.create_new_config)
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_button.setStyleSheet("background-color: #FF9800;")

        file_layout.addWidget(self.file_label)
        file_layout.addWidget(select_button)
        file_layout.addWidget(new_button)
        main_layout.addLayout(file_layout)

        # --- Кнопка вставки VLESS ---
        paste_button = QPushButton("Вставить из буфера (VLESS)")
        paste_button.clicked.connect(self.paste_vless)
        paste_button.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_button.setStyleSheet("background-color: #9C27B0;")
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

        # --- Кнопки действий ---
        button_layout = QHBoxLayout()

        export_btn = QPushButton("Экспорт настроек")
        export_btn.clicked.connect(self.export_settings)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.setStyleSheet("background-color: #FF9800;")

        save_btn = QPushButton("Сохранить изменения")
        save_btn.clicked.connect(self.save_config)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            "font-weight: bold; font-size: 14px; background-color: #4CAF50; color: white; padding: 8px; border-radius: 6px;"
        )

        button_layout.addWidget(export_btn)
        button_layout.addWidget(save_btn)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    # ----------------- Поля -----------------
    def add_field(self, label_text, value, key_path, field_type="text"):
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
        label.setFixedWidth(180)
        label.setStyleSheet("color: #000000; font-weight: bold;")

        layout.addWidget(label)

        key_path_tuple = tuple(key_path)

        if field_type == "checkbox":
            checkbox = QCheckBox()
            # Для SPX: если значение равно "/" или "true" - это True
            if isinstance(value, str):
                checkbox.setChecked(value.lower() in ["true", "/", "1", "yes", "on"])
            else:
                checkbox.setChecked(bool(value))
            layout.addWidget(checkbox)
            self.checkboxes[key_path_tuple] = checkbox
        else:
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
            layout.addWidget(input_field)
            self.inputs[key_path_tuple] = input_field

        self.label_to_key[label_text] = key_path_tuple
        self.scroll_layout.addWidget(frame)

    # ----------------- Создание нового конфига -----------------
    def create_new_config(self):
        path, _ = QFileDialog.getSaveFileName(self, "Создать новый config.json", "", "JSON Files (*.json)")
        if path:
            template = {
                "log": {
                    "loglevel": "warning"
                },
                "inbounds": [
                    {
                        "tag": "socks-inbound",
                        "port": 1080,
                        "listen": "127.0.0.1",
                        "protocol": "socks",
                        "settings": {
                            "auth": "noauth",
                            "udp": True
                        }
                    }
                ],
                "outbounds": [
                    {
                        "tag": "proxy",
                        "protocol": "vless",
                        "settings": {
                            "vnext": [
                                {
                                    "address": "",
                                    "port": 443,
                                    "users": [
                                        {
                                            "id": "",
                                            "encryption": "none",
                                            "flow": ""
                                        }
                                    ]
                                }
                            ]
                        },
                        "streamSettings": {
                            "network": "tcp",
                            "security": "reality",
                            "realitySettings": {
                                "publicKey": "",
                                "shortId": "",
                                "serverName": "",
                                "fingerprint": "chrome",
                                "spx": ""
                            }
                        }
                    }
                ],
                "dns": {
                    "servers": ["8.8.8.8", "1.1.1.1"]
                }
            }

            try:
                self.config_path = Path(path)
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(template, f, indent=4)
                self.file_label.setText(str(self.config_path))
                self.config_data = template
                self.load_config_from_data()
                self.show_message("Успех", "Новый конфиг создан и загружен!")
            except Exception as e:
                self.show_message("Ошибка", f"Не удалось создать файл:\n{e}", icon=QMessageBox.Icon.Critical)

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

            self.load_config_from_data()

        except Exception as e:
            self.show_message("Ошибка", f"Не удалось загрузить config.json:\n{e}", icon=QMessageBox.Icon.Critical)

    def load_config_from_data(self):
        # Очистка старых полей
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.inputs.clear()
        self.checkboxes.clear()
        self.label_to_key.clear()

        # --- Логирование ---
        log = self.config_data.get("log", {})
        self.add_field("Log Level", log.get("loglevel", "warning"), ["log", "loglevel"])

        # --- Inbounds ---
        inbounds = self.config_data.get("inbounds", [])

        # SOCKS inbound
        socks_index = None
        for i, inbound in enumerate(inbounds):
            if inbound.get("protocol") == "socks":
                socks_index = i
                break

        if socks_index is not None:
            inbound = inbounds[socks_index]
            self.add_field("SOCKS Port", inbound.get("port", 1080), ["inbounds", socks_index, "port"])
            self.add_field("SOCKS Listen", inbound.get("listen", "127.0.0.1"), ["inbounds", socks_index, "listen"])
            self.add_field("SOCKS UDP", inbound.get("settings", {}).get("udp", True),
                           ["inbounds", socks_index, "settings", "udp"], "checkbox")
            self.add_field("SOCKS Auth", inbound.get("settings", {}).get("auth", "noauth"),
                           ["inbounds", socks_index, "settings", "auth"])

        # HTTP inbound (если есть)
        http_index = None
        for i, inbound in enumerate(inbounds):
            if inbound.get("protocol") == "http":
                http_index = i
                break

        if http_index is not None:
            inbound = inbounds[http_index]
            self.add_field("HTTP Port", inbound.get("port", 1087), ["inbounds", http_index, "port"])
            self.add_field("HTTP Listen", inbound.get("listen", "127.0.0.1"), ["inbounds", http_index, "listen"])

        # --- DNS Servers ---
        dns_servers = self.config_data.get("dns", {}).get("servers", [])
        for i, server in enumerate(dns_servers[:4]):
            if isinstance(server, str):
                self.add_field(f"DNS Server {i + 1}", server, ["dns", "servers", i])

        # --- Outbounds (ищем VLESS outbound) ---
        outbounds = self.config_data.get("outbounds", [])
        vless_outbound_index = None

        for idx, outbound in enumerate(outbounds):
            if outbound.get("protocol") == "vless":
                vless_outbound_index = idx
                break

        if vless_outbound_index is not None:
            outbound = outbounds[vless_outbound_index]
            self.add_field("Outbound Protocol", outbound.get("protocol", "vless"),
                           ["outbounds", vless_outbound_index, "protocol"])

            vnext = outbound.get("settings", {}).get("vnext", [{}])[0]
            self.add_field("Server Address", vnext.get("address", ""),
                           ["outbounds", vless_outbound_index, "settings", "vnext", 0, "address"])
            self.add_field("Server Port", vnext.get("port", 443),
                           ["outbounds", vless_outbound_index, "settings", "vnext", 0, "port"])

            if "users" in vnext and len(vnext["users"]) > 0:
                user = vnext["users"][0]
                self.add_field("User ID", user.get("id", ""),
                               ["outbounds", vless_outbound_index, "settings", "vnext", 0, "users", 0, "id"])
                self.add_field("Flow", user.get("flow", ""),
                               ["outbounds", vless_outbound_index, "settings", "vnext", 0, "users", 0, "flow"])
                self.add_field("Encryption", user.get("encryption", "none"),
                               ["outbounds", vless_outbound_index, "settings", "vnext", 0, "users", 0, "encryption"])

            stream = outbound.get("streamSettings", {})
            self.add_field("Network", stream.get("network", "tcp"),
                           ["outbounds", vless_outbound_index, "streamSettings", "network"])
            self.add_field("Security", stream.get("security", "reality"),
                           ["outbounds", vless_outbound_index, "streamSettings", "security"])

            reality = stream.get("realitySettings", {})
            self.add_field("Public Key", reality.get("publicKey", ""),
                           ["outbounds", vless_outbound_index, "streamSettings", "realitySettings", "publicKey"])
            self.add_field("Short ID", reality.get("shortId", ""),
                           ["outbounds", vless_outbound_index, "streamSettings", "realitySettings", "shortId"])
            self.add_field("Server Name", reality.get("serverName", ""),
                           ["outbounds", vless_outbound_index, "streamSettings", "realitySettings", "serverName"])
            self.add_field("Fingerprint", reality.get("fingerprint", "chrome"),
                           ["outbounds", vless_outbound_index, "streamSettings", "realitySettings", "fingerprint"])
            self.add_field("SPX", reality.get("spx", ""),
                           ["outbounds", vless_outbound_index, "streamSettings", "realitySettings", "spx"], "checkbox")

        self.show_message("Готово", "Все поля загружены для редактирования!")

    # ----------------- Сохранение -----------------
    def update_nested_value(self, data, key_path, value):
        """Обновляет значение во вложенной структуре, не удаляя другие поля"""
        if not key_path:
            return

        d = data
        for i, key in enumerate(key_path[:-1]):
            if isinstance(key, int):
                if not isinstance(d, list):
                    # Преобразуем в список если нужно
                    d = []
                while len(d) <= key:
                    d.append({})
            elif key not in d:
                d[key] = {}

            if isinstance(key, int):
                d = d[key]
            else:
                d = d[key]

        last_key = key_path[-1]

        # Определяем тип данных
        if last_key in ["udp", "spx"]:
            # Boolean поля
            d[last_key] = bool(value)
        elif last_key in ["port"]:
            # Числовые поля
            try:
                str_value = str(value).strip()
                d[last_key] = int(str_value) if str_value else 0
            except ValueError:
                # Если не число, сохраняем как строку
                d[last_key] = str(value).strip()
        else:
            # Строковые поля
            str_value = str(value).strip()
            d[last_key] = str_value

    def save_config(self):
        if not self.config_path or not self.config_data:
            self.show_message("Ошибка", "Сначала выберите или создайте конфиг файл", icon=QMessageBox.Icon.Warning)
            return

        try:
            # Создаем глубокую копию данных
            import copy
            saved_config = copy.deepcopy(self.config_data)

            # Обновляем текстовые поля
            for key_path, widget in self.inputs.items():
                self.update_nested_value(saved_config, list(key_path), widget.text())

            # Обновляем checkbox поля
            for key_path, checkbox in self.checkboxes.items():
                self.update_nested_value(saved_config, list(key_path), checkbox.isChecked())

            # Сохраняем конфиг
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(saved_config, f, indent=4, ensure_ascii=False)

            # Обновляем текущие данные
            self.config_data = saved_config

            self.show_message("Успех", "Изменения сохранены!")
        except Exception as e:
            self.show_message("Ошибка", f"Не удалось сохранить изменения:\n{e}", icon=QMessageBox.Icon.Critical)

    # ----------------- Вставка VLESS -----------------
    def paste_vless(self):
        if not self.config_data:
            self.show_message("Ошибка", "Сначала загрузите или создайте конфиг файл", icon=QMessageBox.Icon.Warning)
            return

        clipboard = QApplication.clipboard()
        vless_url = clipboard.text().strip()

        if not vless_url.startswith("vless://"):
            self.show_message("Ошибка", "В буфере нет ссылки VLESS", icon=QMessageBox.Icon.Warning)
            return

        try:
            # Удаляем комментарий если есть
            if '#' in vless_url:
                vless_url = vless_url.split('#')[0]

            # Парсим с помощью регулярных выражений
            pattern = r'vless://([^@]+)@([^:/]+):(\d+)\?(.+)'
            match = re.match(pattern, vless_url)

            if not match:
                # Пробуем альтернативный паттерн
                pattern = r'vless://([^@]+)@([^:]+):(\d+)'
                match = re.match(pattern, vless_url)
                if not match:
                    self.show_message("Ошибка", "Неверный формат VLESS ссылки", icon=QMessageBox.Icon.Warning)
                    return
                params_str = ""
            else:
                params_str = match.group(4)

            uuid = urllib.parse.unquote(match.group(1))
            host = match.group(2)
            port = match.group(3)

            # Парсим параметры
            params = {}
            if params_str:
                for param in params_str.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = urllib.parse.unquote(value)

            # Маппинг на поля в интерфейсе
            field_mapping = {
                "User ID": uuid,
                "Server Address": host,
                "Server Port": port,
                "Network": params.get('type', ''),
                "Security": params.get('security', ''),
                "Public Key": params.get('pbk', ''),
                "Fingerprint": params.get('fp', ''),
                "Server Name": params.get('sni', ''),
                "Short ID": params.get('sid', ''),
                "SPX": params.get('spx', ''),
                "Flow": params.get('flow', ''),
                "Encryption": params.get('encryption', 'none')
            }

            # Заполняем поля
            updated = 0
            for field_name, value in field_mapping.items():
                if value:
                    if field_name in self.label_to_key:
                        key_path = self.label_to_key[field_name]
                        if key_path in self.inputs:
                            self.inputs[key_path].setText(value)
                            updated += 1
                        elif key_path in self.checkboxes:
                            # Для SPX - если значение "/", это True
                            self.checkboxes[key_path].setChecked(value == '/')
                            updated += 1

            if updated > 0:
                # Показываем какие поля были обновлены
                updated_fields = []
                for field_name in field_mapping:
                    if field_name in self.label_to_key and field_mapping[field_name]:
                        updated_fields.append(field_name)

                message = f"Обновлено {updated} полей:\n"
                for field in updated_fields[:5]:  # Показываем первые 5 полей
                    value = field_mapping[field]
                    if field == "User ID":
                        value = f"{value[:8]}..."
                    elif field == "Public Key":
                        value = f"{value[:8]}..."
                    message += f"• {field}: {value}\n"

                if len(updated_fields) > 5:
                    message += f"• ... и еще {len(updated_fields) - 5} полей\n"

                self.show_message("Успех", message)
            else:
                self.show_message("Ошибка",
                                  "Не удалось заполнить поля.\n"
                                  "Убедитесь что вы загрузили конфиг файл.\n"
                                  f"Доступные поля: {list(self.label_to_key.keys())}",
                                  icon=QMessageBox.Icon.Warning)

        except Exception as e:
            self.show_message("Ошибка", f"Ошибка при парсинге VLESS ссылки:\n{str(e)}", icon=QMessageBox.Icon.Critical)

    # ----------------- Экспорт настроек -----------------
    def export_settings(self):
        if not self.config_data:
            self.show_message("Ошибка", "Нет данных для экспорта", icon=QMessageBox.Icon.Warning)
            return

        path, _ = QFileDialog.getSaveFileName(self, "Экспорт настроек", "xray_config_export.json",
                                              "JSON Files (*.json)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.config_data, f, indent=4, ensure_ascii=False)
                self.show_message("Успех", "Настройки экспортированы!")
            except Exception as e:
                self.show_message("Ошибка", f"Не удалось экспортировать:\n{e}", icon=QMessageBox.Icon.Critical)

    # ----------------- Сообщения -----------------
    def show_message(self, title, text, icon=QMessageBox.Icon.Information):
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 12pt;
            }
            QPushButton {
                min-width: 80px;
                padding: 5px;
            }
        """)
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
                padding: 8px 12px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QCheckBox {
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = FullXrayEditor()
    editor.show()
    sys.exit(app.exec())