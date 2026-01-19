## Xray Full Config Editor 
#### Графический инструмент для удобного редактирования config.json файлов Xray Core.
Основные возможности
### 1. Управление Inbounds
- Редактирование порта (port), на котором слушает сервер.
- Настройка адреса для прослушивания (listen).
- Выбор протокола (protocol).
- Поддержка включения/отключения UDP (settings.udp).
### 2. Управление Outbounds
- Изменение протокола исходящих соединений (protocol).
- Редактирование VNext-серверов:
- Адрес (address) и порт (port) сервера.
- ID пользователя (id), поток (flow) и метод шифрования (encryption).
- Настройка Stream Settings:
- Сеть (network), безопасность (security).
- Настройки Reality (realitySettings):
- Публичный ключ (publicKey), ShortID (shortId), ServerName (serverName), Fingerprint, SPX.
### 3. Работа с VLESS ссылками
- Поддержка вставки ссылок формата:
````
vless://<USER_ID>@<HOST>:<PORT>?type=<NETWORK>&security=<SECURITY>&pbk=<PUBLIC_KEY>&fp=<FINGERPRINT>&sni=<SERVER_NAME>&sid=<SHORT_ID>&spx=<SPX>#<NAME>
````
- Редактируются только те поля, которые указаны в ссылке.
- Остальные поля остаются без изменений.
### 4. Сохранение конфигурации
- Изменения сохраняются прямо в исходный config.json.
- Автоматическая проверка типа данных (числа, булевы значения).
- Ошибки в сохранении отображаются в диалоговом окне.
### 5. Удобный интерфейс
- Поля организованы в скроллируемом окне, удобно редактировать большие конфиги.
- Современный светлый дизайн.
- Черный текст на белом фоне для максимальной читаемости.
- Все элементы имеют аккуратные рамки и отступы.
- Кнопки с визуальной подсветкой и hover-эффектом.
### Дополнительно
- Минимизирует риск ошибок при редактировании конфигурации вручную.
### Установка и запуск
### 1. Клонируем репозиторий
````
git clone https://github.com/<ваш-username>/xray-config-editor.git
cd xray-config-editor
````
### 2. Создаем виртуальное окружение (рекомендовано)
````
# Устанавливаем venv, если ещё не установлен
sudo apt update
sudo apt install python3.12-venv

# Создаем виртуальное окружение
python3 -m venv venv

# Активируем окружение
source venv/bin/activate
````
### 3. Устанавливаем зависимости
````
pip install PyQt6
````
### 4. Запускаем редактор
````
python full_xray_editor.py
````
- Можно также запускать напрямую без активации окружения:
````
./venv/bin/python full_xray_editor.py
````
---
![Start](https://github.com/MLewickiy/EditXrayConfig/blob/master/pix/start.png)
![Start](https://github.com/MLewickiy/EditXrayConfig/blob/master/pix/create.png)
