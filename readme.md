# <h1 align="center">Deepway Telegram Bot</h1>

<p align="center">
    An advanced Telegram bot that helps users connect with new people, discover Telegram channels and groups, and buy access to exclusive content. Inspired by popular friend-matching bots, but enhanced with group discovery and monetization features.
</p>

<p align="center">
<a href="https://www.python.org/downloads/release/python-3110/" target="_blank"><img src="https://img.shields.io/badge/Python-3.11-blue" alt="Python 3.11" /></a>
<a href="https://docs.aiogram.dev/en/latest/" target="_blank"><img src="https://img.shields.io/badge/Aiogram-2.25.2-green" alt="Aiogram 2.25.2" /></a>
<a href="https://docs.aiohttp.org/en/stable/" target="_blank"><img src="https://img.shields.io/badge/Aiohttp-3.8.6-lightgrey" alt="aiohttp 3.8.6" /></a>
<a href="https://pypi.org/project/python-dotenv/" target="_blank"><img src="https://img.shields.io/badge/dotenv-1.1-yellow" alt="dotenv 1.1" /></a>
<a href="https://pypi.org/project/mysql-connector-python/" target="_blank"><img src="https://img.shields.io/badge/MySQLConnector-9.2-orange" alt="mysql-connector-python 9.2" /></a>
<a href="https://pypi.org/project/cryptography/" target="_blank"><img src="https://img.shields.io/badge/Cryptography-44.2-red" alt="cryptography 44.0.2" /></a>
<a href="https://www.jetbrains.com/pycharm/" target="_blank"><img src="https://img.shields.io/badge/IDE-PyCharm-brightgreen" alt="PyCharm" /></a>
</p>

![Deepway](/banner.jpg)

---

## ✨ Key Features

- **📡 Media Discovery:** Browse Telegram channels and groups added by users.
- **🔐 Private Media:** Mark groups/channels as private and restrict access.
- **💸 Access Marketplace:** Users can purchase access to selected private channels/groups.
- **🔐 Secure Data:** Uses `cryptography` for secure token handling and sensitive operations.

---

## 🚀 Quick Start

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/eXdesy/DeepwayTelegramBot.git
    cd Deepway
    ```

2. **Set Up Virtual Environment:**

    ```bash
    python -m venv .venv

    # Windows
    .venv\Scripts\activate

    # macOS/Linux
    source .venv/bin/activate
    ```

3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure Environment Variables:**

    Create a `.env` file and set the following variables:

    ```env
    BOT_TOKEN=your_bot_token
    FERNET_TOKEN=your_token_key
    DB_HOST=localhost
    DB_PORT=3306
    DB_USER=your_user
    DB_PASSWORD=your_password
    DB_NAME=your_database
    ```

5. **Run the Bot:**

    ```bash
    python main.py
    ```

---

## ⚙️ System Overview

The **Deepway** integrates the following components:

### 🔐 TokenHandler

- Securely manages the bot token and other sensitive values.  
- Interacts with `.env` configuration using `python-dotenv`.

### 🗃️ SQLHandler

- Handles all MySQL interactions (read/write).  
- Executes queries to manage users, channels, and access logic.  
- Uses `mysql-connector-python` for database communication.

### 💾 LocalDataHandler

- Manages local user session data and caching.  
- Useful for temporary storage without database overhead.

### 🌐 Language Modules

- Provides multilingual support for bot messages.  
- Available languages: **English (US, UK)**, **Spanish (ES)**, **Russian (RU)**.  
- Easy to extend with new languages in `languages/`.

---

## 🧩 Features in Detail

- **Matchmaking System**
  - Users are matched by preferences (age, region, tags).
  - Anonymized interactions with follow-up options.

- **User-Contributed Channels**
  - Each user can submit a group or channel.
  - Others can browse and search via keywords or tags.

- **Premium Content**
  - Some groups/channels marked as "paid access."
  - Payment logic can be integrated via Telegram's `payments` or third-party services.

---

## 💡 Notes

- Bot requires a running **MySQL 8+ server**.
- All user data is stored in a structured and encrypted manner.
- The system is modular and easy to expand with new features.

---

## 🔒 License

This project is licensed under a custom "read-only" license by **eXdesy**.

📌 **Do not reuse, modify, or distribute this code.**  
It is provided **strictly for educational purposes**.

See the full terms in the [`LICENSE`](./LICENSE) file.

<h2 align="center">All rights reserved by eXdesy</h2>


