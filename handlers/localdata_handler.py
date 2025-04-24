# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
from aiogram import types
from dataclasses import dataclass
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup

from handlers.sql_handler import *
from configs import bot

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

async def handle_isinstance(entity, telegram_id):
    chat_id = None
    message_id = None
    current_message_id = fetch_log_states_data(telegram_id, 'current_message_id')
    current_language = fetch_log_states_data(telegram_id, 'current_language')
    current_state = fetch_log_states_data(telegram_id, 'current_state')
    temporal_state = fetch_log_states_data(telegram_id, 'temporal_state')
    current_action = fetch_log_states_data(telegram_id, 'current_action')
    current_media_id = fetch_log_states_data(telegram_id, 'current_media_id')
    current_media_type_id = fetch_log_states_data(telegram_id, 'current_media_type_id')
    current_media_type = fetch_log_states_data(telegram_id, 'current_media_type')
    current_media_data = fetch_log_states_data(telegram_id, 'current_media_data')
    current_media_index = fetch_log_states_data(telegram_id, 'current_media_index')
    not_callback = None
    if isinstance(entity, types.CallbackQuery):
        chat_id = entity.message.chat.id
        message_id = entity.message.message_id
    if isinstance(entity, types.Message):
        chat_id = entity.chat.id
        message_id = entity.message_id
        not_callback = True

    return IsInstanceResult(chat_id, message_id, current_message_id, current_language, current_state, temporal_state,
                            current_action,
                            current_media_id, current_media_type_id, current_media_type, current_media_data,
                            current_media_index, not_callback)

async def edit_entity_message_media(chat_id, message_id, media_data, caption, markup_inline=None, current_language=None,
                                    delete_message=None, back_button=None, edit_message=None, fixed_message_id=None):
    if delete_message:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    if markup_inline is None:
        markup_inline = InlineKeyboardMarkup()
    if back_button:
        markup_inline.row(InlineKeyboardButton(text=current_language.backButton, callback_data='back'))
    if fixed_message_id:
        message_id = fixed_message_id

    with open(media_data, 'rb') as media:
        if edit_message:
            await bot.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=types.InputMediaPhoto(media, caption=caption, parse_mode='HTML'),
                reply_markup=markup_inline
            )
        else:
            await bot.send_photo(
                chat_id=chat_id,
                photo=media,
                caption=caption,
                parse_mode='HTML',
                reply_markup=markup_inline
            )

async def handle_media_recommendations(telegram_id, media_type):
    """
    Calculates a recommendation score for each media_id (channel or group) based on the following criteria:
      - +0.5% for each subscriber (equivalent to +5% per 10 subscribers)
      - -0.5% for each complaint (equivalent to -5% per 10 complaints)
      - +40% if the media category matches the user's subscriptions
      - +20% if the media was created within the last 30 days
      - +10% if the media owner is verified
      - +20% if the media owner has Boost status

    :param telegram_id: Telegram user ID.
    :param media_type: Type of media ('groups' or 'channels').
    :return: A list of tuples (media, score), sorted by score in descending order.
    """
    # 1. Get subscription counts for each media
    subscriptions_result = count_media_subscriptions(media_type)
    # Should return a list of tuples: [(media_id, subscription_count), ...]
    subs_dict = {row[0]: row[1] for row in subscriptions_result} if subscriptions_result else {}

    # 2. Get report counts for each media
    reports_result = count_media_reports(media_type)
    # Should return a list of tuples: [(media_id, report_count), ...]
    reports_dict = {row[0]: row[1] for row in reports_result} if reports_result else {}

    # 3. Get the list of categories the user is subscribed to
    user_categories_result = fetch_user_subscription_category(telegram_id, media_type)
    # Expected to return a list of tuples, e.g. [(category1,), (category2,), ...]
    user_categories = {row[0] for row in user_categories_result} if user_categories_result else set()

    # 4. Get a set of media_id created within the last 30 days
    recent_result = fetch_recent_media_ids(media_type)
    # Should return a list of tuples: [(media_id,), ...]
    recent_media_ids = {row[0] for row in recent_result} if recent_result else set()

    # 5. Get a set of media_id owned by verified users
    verified_user_result = fetch_verified_user_media(media_type)
    # Should return a list of tuples: [(media_id,), ...]
    verified_user_media_ids = {row[0] for row in verified_user_result} if verified_user_result else set()

    # 6. Get a set of media_id owned by users with Boost status
    boosted_result = fetch_boosted_media(media_type)
    # Should return a list of tuples: [(media_id,), ...]
    boosted_media_ids = {row[0] for row in boosted_result} if boosted_result else set()

    # 7. Get all media_id and their categories from the corresponding table
    all_media = fetch_all_media_id(media_type)
    # Should return a list of tuples: [(media_id, category), ...]

    recommendations = []
    score = 0
    for media_id, category in all_media:
        # Add +0.5% per subscriber (equivalent to +5% for every 10)
        subs = subs_dict.get(media_id, 0)
        score += subs * 0.5

        # Subtract -0.5% per complaint (equivalent to -5% for every 10)
        rep = reports_dict.get(media_id, 0)
        score -= rep * 0.5

        # If the media category matches user's subscriptions, add +40%
        if category in user_categories:
            score += 40

        # If the media was created in the last 30 days, add +20%
        if media_id in recent_media_ids:
            score += 20

        # If the media owner is verified, add +10%
        if media_id in verified_user_media_ids:
            score += 10

        # If the media owner has Boost status, add +20%
        if media_id in boosted_media_ids:
            score += 20

        recommendations.append((media_id, score))

    # Sort the list by score in descending order
    recommendations.sort(key=lambda x: x[1], reverse=True)
    # Return only the list of media_id
    return [media_id for media_id, score in recommendations]
