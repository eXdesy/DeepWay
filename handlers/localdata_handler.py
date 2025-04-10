# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
from aiogram.dispatcher.filters.state import State, StatesGroup
from dataclasses import dataclass

@dataclass
class IsInstanceResult:
    chat_id: any
    message_id: any
    current_message_id: any
    current_language: any
    current_state: any
    temporal_state: any
    current_action: any
    current_media_id: any
    current_media_type_id: any
    current_media_type: any
    current_media_data: any
    current_media_index: any
    not_callback: any

    def __getitem__(self, key):
        # Доступ по индексу
        if isinstance(key, int):
            return (self.chat_id,
                    self.message_id,
                    self.current_message_id,
                    self.current_language,
                    self.current_state,
                    self.temporal_state,
                    self.current_action,
                    self.current_media_id,
                    self.current_media_type_id,
                    self.current_media_type,
                    self.current_media_data,
                    self.current_media_index,
                    self.not_callback
                    )[key]
        # Доступ по ключу (атрибуту)
        elif isinstance(key, str):
            return getattr(self, key)
        else:
            raise KeyError(f"Invalid key type: {key}")

class UserStates(StatesGroup):
    waiting_for_support = State()
    waiting_for_register = State()
    waiting_for_login = State()
    waiting_for_restore_account = State()
    waiting_for_update_username = State()
    waiting_for_validate_user_password = State()
    waiting_for_update_user_password = State()

class MediaStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_photo = State()
    waiting_for_category = State()
    waiting_for_price = State()
    waiting_for_planes = State()

user_recommendations = {}
def user_recommendation_data(telegram_id):
    if telegram_id not in user_recommendations:
        user_recommendations[telegram_id] = {}
    return user_recommendations[telegram_id]

add_media = {}
def add_media_data(telegram_id):
    if telegram_id not in add_media:
        add_media[telegram_id] = {
            'plan1_price': 0,
            'plan3_price': 0,
            'plan6_price': 0,
            'plan12_price': 0,
            'plan_price': 0
        }
    return add_media[telegram_id]
