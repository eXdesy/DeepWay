# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
import os
from dotenv import load_dotenv
from aiogram import Bot
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

usButton = 'ENGLISH 🇺🇸'
ruButton = 'РУССКИЙ 🇷🇺'
esButton = 'ESPAÑOL 🇪🇸'
uaButton = 'УКРАЇНСЬКА 🇺🇦'
languageMenuText = (
    '🇺🇸 Choose your the language\n'
    '🇷🇺 Выберите свой язык\n'
    '🇪🇸 Elige tu idioma\n'
    '🇺🇦 Оберіть свою мову\n\n'
    '💡 You can change the language anytime in the settings.'
)
languageMenuMedia = r'media\language.png'
