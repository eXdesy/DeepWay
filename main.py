# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from datetime import datetime, timedelta
from io import BytesIO
import asyncio
from aiogram.dispatcher import FSMContext
from urllib.parse import urlencode
import aiohttp

from configs import *
from handlers.sql_handler import *
from handlers.token_handler import *
from handlers.localdata_handler import *

import logging
logging.basicConfig()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    telegram_id = message.from_user.id

    if fetch_log_states_data(telegram_id, 'current_telegram_id') is False:
        create_log_states(telegram_id, None, None, None, None, None, None, None, None, None, None, datetime.now())

    if fetch_log_states_data(telegram_id, 'current_language'):
        token = fetch_user_token(telegram_id)
        if token:
            decrypt_token(token)
            await menu_(message, 'main')
        else:
            await menu_(message, 'login')
    else:
        await menu_(message, 'language')

############################## HANDLE ACCOUNT ##############################
@dp.callback_query_handler(Text(startswith='menu_'))
async def menu_(entity, menu_type=None):
    if menu_type is None:
        menu_type = entity.data.split('_')[1]
    telegram_id = entity.from_user.id
    result = await handle_isinstance(entity, telegram_id)

    edit_message = None if result.not_callback else True
    current_language = None
    delete_message = None
    back_button = None
    fixed_message_id = None
    media_data = ''
    caption = ''

    markup_inline = InlineKeyboardMarkup(row_width=2)
    if menu_type == 'login':
        update_log_states_data(telegram_id, 'login', 'current_state')
        media_data = result.current_language.loginMenuMedia
        caption = result.current_language.loginMenuText

        markup_inline.add(
            InlineKeyboardButton(text=result.current_language.loginButton, callback_data='login'),
            InlineKeyboardButton(text=result.current_language.restoreAccountButton, callback_data='restore_account'),
            InlineKeyboardButton(text=result.current_language.supportButton, callback_data='support_')
        )

    elif menu_type == 'main' and fetch_user_token(telegram_id):
        update_log_states_data(telegram_id, 'main', 'current_state')
        media_data = result.current_language.mainMenuMedia
        caption = result.current_language.mainMenuText

        if result.current_state == 'menu_login' or result.temporal_state == 'update_user_password':
            update_log_states_data(telegram_id, None, 'temporal_state')
            edit_message = True
            delete_message = True
            fixed_message_id = result.current_message_id

        markup_inline.add(
            InlineKeyboardButton(text=result.current_language.searchMediaButton, callback_data='menu_media'),
            InlineKeyboardButton(text=result.current_language.supportButton, callback_data='support_user'),
            InlineKeyboardButton(text=result.current_language.accountButton, callback_data='menu_user')
        )

    elif menu_type == 'language':
        media_data = languageMenuMedia
        caption = languageMenuText

        markup_inline.add(
            InlineKeyboardButton(text=usButton, callback_data='language_us'),
            InlineKeyboardButton(text=ruButton, callback_data='language_ru'),
            InlineKeyboardButton(text=esButton, callback_data='language_es'),
            InlineKeyboardButton(text=uaButton, callback_data='language_uk')
        )

        if result.not_callback is None:
            update_log_states_data(telegram_id, 'menu_user', 'current_state')
            fixed_message_id = result.message_id
            current_language = result.current_language
            back_button = True

    elif menu_type == 'user' and fetch_user_token(telegram_id):
        update_log_states_data(telegram_id, 'menu_main', 'current_state')
        media_data = result.current_language.userMenuMedia
        username, subscription_count = count_user_subscriptions(telegram_id)
        if username:
            verification = verify_user_data(telegram_id, True, 'verification')
            verification_status = result.current_language.isVerifiedText if verification == True else result.current_language.isNotVerifiedText

            if verify_user_boost(telegram_id):
                boost_date = fetch_boost_expire_date(telegram_id)
                boost_status = result.current_language.isBoostedText.format(boost_date=boost_date.strftime('%Y-%m-%d'))
            else:
                boost_status = result.current_language.isNotBoostedText

            caption = result.current_language.accountText.format(
                username=username,
                verification_status=verification_status,
                subscription_count=subscription_count,
                boost_status=boost_status
            )
        else:
            caption = result.current_language.noAccountText

        markup_inline.add(
            InlineKeyboardButton(text=result.current_language.updatePasswordButton, callback_data='password'),
            InlineKeyboardButton(text=result.current_language.updateLanguageButton, callback_data='menu_language'),
            InlineKeyboardButton(text=result.current_language.subscriptionsButton, callback_data='menu_subscriptions'),
            InlineKeyboardButton(text=result.current_language.userMediaButton, callback_data='menu_userMedia'),
            InlineKeyboardButton(text=result.current_language.logoutButton, callback_data='logout'),
            InlineKeyboardButton(text=result.current_language.backButton, callback_data='back')
        )

    elif menu_type == 'media' and fetch_user_token(telegram_id):
        update_log_states_data(telegram_id, 'menu_main', 'current_state')
        media_data = result.current_language.mediaMenuMedia
        caption = result.current_language.mediaMenuText
        current_language = result.current_language
        back_button = True

        markup_inline.add(
            InlineKeyboardButton(text=result.current_language.channelsButton, callback_data='media_channels'),
            InlineKeyboardButton(text=result.current_language.groupsButton, callback_data='media_groups')
        )

    elif menu_type == 'userMedia' and fetch_user_token(telegram_id):
        update_log_states_data(telegram_id, 'menu_user', 'current_state')
        media_data = result.current_language.userMediaMenuMedia
        caption = result.current_language.userMediaMenuText
        current_language = result.current_language
        back_button = True

        markup_inline.add(
            InlineKeyboardButton(text=result.current_language.channelsButton, callback_data='user_media_channels'),
            InlineKeyboardButton(text=result.current_language.groupsButton, callback_data='user_media_groups')
        )

        auth_url = await vinculate_DA(telegram_id)
        markup_inline.row(
            InlineKeyboardButton("🔗 Подключить Donation Alerts", url=auth_url),
            InlineKeyboardButton(text=result.current_language.boostButton, callback_data='boost')
        )

    elif menu_type == 'subscriptions' and fetch_user_token(telegram_id):
        update_log_states_data(telegram_id, 'menu_user', 'current_state')
        media_data = result.current_language.subscriptionsMenuMedia
        caption = result.current_language.subscriptionsMenuText
        current_language = result.current_language
        back_button = True

        markup_inline.add(
            InlineKeyboardButton(text=result.current_language.channelsButton,
                                 callback_data='subscriptions_list_channels'),
            InlineKeyboardButton(text=result.current_language.groupsButton, callback_data='subscriptions_list_groups')
        )

    else:
        await start(entity)

    await edit_entity_message_media(result.chat_id, result.message_id, media_data, caption, markup_inline,
                                    current_language=current_language,
                                    delete_message=delete_message, back_button=back_button, edit_message=edit_message,
                                    fixed_message_id=fixed_message_id)

@dp.callback_query_handler(Text(equals='boost'))
async def boost(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_user_media', 'current_state')

    markup_inline = InlineKeyboardMarkup()
    markup_inline.row(
        InlineKeyboardButton(text=result.current_language.checkPaymentButton, callback_data=f'check_payment_boost'))

    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.boostMedia,
                                    result.current_language.boostText, current_language=result.current_language,
                                    back_button=True, edit_message=True, markup_inline=None)

@dp.callback_query_handler(Text(startswith='support_'))
async def support_(callback_query: types.CallbackQuery):
    action = callback_query.data.split('_')[1]
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')

    update_log_states_data(telegram_id, 'menu_main', 'current_state') if action == 'user' \
        else update_log_states_data(telegram_id, 'menu_login', 'current_state')

    update_log_states_data(telegram_id, 'support', 'temporal_state')
    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.supportMedia,
                                    result.current_language.supportText, current_language=result.current_language,
                                    back_button=True, edit_message=True)

@dp.callback_query_handler(Text(equals='report'))
async def report(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'media_', 'current_state')

    media_id = fetch_log_states_data(telegram_id, 'current_media_id')
    media_type = fetch_log_states_data(telegram_id, 'current_media_type')

    types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
    chat_info = await bot.get_chat(media_id)
    title = chat_info.title

    caption = result.current_language.reportText.format(
        channel_name=title,
        media_type=types
    )

    update_log_states_data(telegram_id, 'report', 'temporal_state')
    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.reportMedia, caption,
                                    current_language=result.current_language, back_button=True, edit_message=True)

@dp.callback_query_handler(Text(equals='restore_account'))
async def restore_account(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_login', 'current_state')

    update_log_states_data(telegram_id, 'restore_account', 'temporal_state')
    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.restoreAccountMedia,
                                    result.current_language.restoreAccountText,
                                    current_language=result.current_language, back_button=True, edit_message=True)

@dp.callback_query_handler(Text(equals='password'))
async def password(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_user', 'current_state')

    update_log_states_data(telegram_id, 'validate_user_password', 'temporal_state')
    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.passwordMedia,
                                    result.current_language.updatePasswordText,
                                    current_language=result.current_language, back_button=True, edit_message=True)

@dp.callback_query_handler(Text(equals='login'))
async def login(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    username = callback_query.from_user.username
    result = await handle_isinstance(callback_query, telegram_id)
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_login', 'current_state')

    if verify_user(telegram_id):
        menuMedia = result.current_language.loginMedia
        if verify_user_data(telegram_id, username, 'username'):
            update_log_states_data(telegram_id, username, 'current_action')

            caption = result.current_language.loginText
            update_log_states_data(telegram_id, 'login', 'temporal_state')
        else:
            caption = result.current_language.usernameErrorText
            update_log_states_data(telegram_id, 'update_username', 'temporal_state')
    else:
        menuMedia = result.current_language.registerMedia
        if username:
            update_log_states_data(telegram_id, username, 'current_action')
            caption = result.current_language.registerText
            update_log_states_data(telegram_id, 'register', 'temporal_state')
        else:
            caption = result.current_language.usernameErrorText

    await edit_entity_message_media(result.chat_id, result.message_id, menuMedia, caption,
                                    current_language=result.current_language, back_button=True, edit_message=True)

@dp.callback_query_handler(Text(startswith='language_'))
async def language_(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    update_log_states_data(telegram_id, callback_query.data, 'current_language')
    await start(callback_query)

@dp.callback_query_handler(Text(equals='logout'))
async def logout(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    clear_user_session(telegram_id)
    await start(callback_query)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('subscriptions_list'))
async def subscriptions_list(entity):
    media_type = entity.data.split('_')[2]
    data_parts = entity.data.split('_')
    page = 0
    if len(data_parts) >= 3 and data_parts[-1].isdigit():
        page = int(data_parts[-1])

    telegram_id = entity.from_user.id
    result = await handle_isinstance(entity, telegram_id)
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_subscriptions', 'current_state')

    markup_inline = InlineKeyboardMarkup(row_width=2)
    if fetch_user_token(telegram_id):

        if result.current_state == 'menu_media':
            update_log_states_data(telegram_id, 'media_', 'current_state')
            media_type = fetch_log_states_data(telegram_id, 'current_media_type')
            types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
            caption = result.current_language.alreadyJoinedText.format(media_type=types)
            await entity.answer(caption, show_alert=True)
        if result.current_state == 'media_':
            update_log_states_data(telegram_id, 'media_', 'current_state')

        caption = result.current_language.subscriptionTitleText
        subscriptions = fetch_user_subscriptions(telegram_id, media_type)
        if subscriptions:
            PAGE_SIZE = 3
            total = len(subscriptions)
            init = page * PAGE_SIZE
            end = init + PAGE_SIZE
            page_subscriptions = subscriptions[init:end]

            buttons = []
            for media_id, subscription_date, expire_date, link in page_subscriptions:
                group = await bot.get_chat(chat_id=media_id)
                formatted_sub_date = subscription_date.strftime(
                    '%d %b %Y') if subscription_date else result.current_language.foreverButton
                formatted_exp_date = expire_date.strftime(
                    '%d %b %Y') if expire_date else result.current_language.foreverButton
                caption += result.current_language.subscriptionText.format(
                    group_title=group.title,
                    formatted_sub_date=formatted_sub_date,
                    formatted_exp_date=formatted_exp_date
                )
                buttons.append(InlineKeyboardButton(text=group.title, url=link))

            if page > 0:
                buttons.append(InlineKeyboardButton(result.current_language.previousButton,
                                                    callback_data=f'subscriptions_list_{media_type}_{page - 1}'))
            if end < total:
                buttons.append(InlineKeyboardButton(result.current_language.nextButton,
                                                    callback_data=f'subscriptions_list_{media_type}_{page + 1}'))

            for i in range(0, len(buttons), 2):
                markup_inline.add(*buttons[i:i + 2])
        else:
            caption += result.current_language.noSubscriptionText

        await edit_entity_message_media(result.chat_id, result.message_id,
                                        result.current_language.subscriptionsMenuMedia,
                                        caption, markup_inline=markup_inline, current_language=result.current_language,
                                        back_button=True, edit_message=True)
    else:
        await start(entity)

@dp.message_handler(lambda message: fetch_log_states_data(message.from_user.id, 'temporal_state') is not None,
                    content_types=types.ContentType.ANY)
async def handle_login(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    login_state = fetch_log_states_data(message.from_user.id, 'temporal_state')
    result = await handle_isinstance(message, telegram_id)

    status = 'user'
    verification = False
    media_data = ''
    caption = ''
    token = generate_token(telegram_id, status)
    donation_alerts_token = ''

    if login_state == 'support':
        support_description = message.text
        create_support_request(telegram_id, username, support_description, datetime.now())
        support_id = fetch_support_id(telegram_id)
        media_data = result.current_language.supportMedia
        caption = result.current_language.supportAnswerText.format(
            support_id=support_id
        )

        update_log_states_data(telegram_id, None, 'temporal_state')

    elif login_state == 'report':
        report_description = message.text
        create_media_report(telegram_id, username, result.current_media_id, report_description,
                            result.current_media_type, datetime.now())
        media_data = result.current_language.reportMedia
        caption = result.current_language.reportAnswerText

        update_log_states_data(telegram_id, None, 'temporal_state')

    elif login_state == 'register':
        password = message.text

        username = fetch_log_states_data(telegram_id, 'current_action')
        backup_code = generate_backup_code()

        register_user(telegram_id, username, password, status, verification, backup_code, token, donation_alerts_token, datetime.now())
        create_log_users(telegram_id, telegram_id, True, 'register', datetime.now())

        await start(message)
        update_log_states_data(telegram_id, None, 'temporal_state')
        update_log_states_data(telegram_id, None, 'current_action')
        return

    elif login_state == 'login':
        password = message.text
        old_username = fetch_log_states_data(telegram_id, 'current_action')
        user_telegram_id = fetch_user_telegram_id(username, password, 'password')

        if verify_user_data(telegram_id, password, 'password'):
            login_and_update_user_session(telegram_id, username, token, password, old_username)
            create_log_users(telegram_id, user_telegram_id, True, 'login', datetime.now())

            await start(message)
            update_log_states_data(telegram_id, None, 'temporal_state')
            update_log_states_data(telegram_id, None, 'current_action')
            return
        else:
            create_log_users(telegram_id, user_telegram_id, False, 'login', datetime.now())
            media_data = result.current_language.errorMedia
            caption = result.current_language.passwordErrorText

    elif login_state == 'restore_account':
        backup_code = message.text
        user_telegram_id = fetch_user_telegram_id(username, backup_code, 'backup_code')

        if verify_user_data(telegram_id, backup_code, 'backup_code'):
            restore_user_account(telegram_id, token, backup_code)
            create_log_users(telegram_id, user_telegram_id, True, 'restore_account', datetime.now())

            await start(message)
            update_log_states_data(telegram_id, None, 'temporal_state')
            return
        else:
            create_log_users(telegram_id, user_telegram_id, False, 'restore_account', datetime.now())
            media_data = result.current_language.errorMedia
            caption = result.current_language.restoreAccountErrorText

    elif login_state == 'update_username':
        old_username = message.text
        if verify_user_data(telegram_id, old_username, 'username'):
            caption = result.current_language.usernameVerifiedText
            media_data = result.current_language.loginMedia
            update_log_states_data(telegram_id, old_username, 'current_action')
            update_log_states_data(telegram_id, 'login', 'temporal_state')
        else:
            caption = result.current_language.usernameErrorText
            media_data = result.current_language.errorMedia

    elif login_state == 'validate_user_password':
        password = message.text
        if verify_user_data(telegram_id, password, 'password') or verify_user_data(telegram_id, password,
                                                                                   'backup_code'):
            caption = result.current_language.newPasswordText
            media_data = result.current_language.passwordMedia
            update_log_states_data(telegram_id, 'update_user_password', 'temporal_state')
        else:
            caption = result.current_language.updatePasswordErrorText
            media_data = result.current_language.errorMedia

    elif login_state == 'update_user_password':
        new_password = message.text
        update_user_data(telegram_id, new_password, 'password')
        await start(message)
        return

    await edit_entity_message_media(result.chat_id, result.message_id, media_data, caption, delete_message=True,
                                    current_language=result.current_language, back_button=True, edit_message=True,
                                    fixed_message_id=result.current_message_id)

############################## HANDLE MEDIA ##############################
@dp.callback_query_handler(Text(startswith='user_media_'))
async def user_media_(callback_query: types.CallbackQuery, media_type=None):
    telegram_id = callback_query.from_user.id
    if media_type is None:
        media_type = callback_query.data.split('_')[2]

    update_log_states_data(telegram_id, media_type, 'current_media_type')
    result = await handle_isinstance(callback_query, telegram_id)
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_user_media', 'current_state')

    if fetch_user_token(telegram_id):
        media = fetch_user_media(telegram_id, result.current_media_type, result.current_media_id)

        markup_inline = InlineKeyboardMarkup()
        if media:
            markup_inline.row(
                InlineKeyboardButton(result.current_language.previousButton, callback_data='prev_media'),
                InlineKeyboardButton(result.current_language.nextButton, callback_data='next_media')
            )
            markup_inline.row(
                InlineKeyboardButton(result.current_language.editButton, callback_data=f'update_user_media_'),
                InlineKeyboardButton(result.current_language.deleteButton, callback_data=f'delete_media'),
                InlineKeyboardButton(result.current_language.addMediaButton, callback_data='create_user_media_')
            )
        else:
            await create_user_media_(callback_query)
            return

        await display_media(callback_query, markup_inline, media)
    else:
        await start(callback_query)

@dp.callback_query_handler(Text(startswith='media_'))
async def media_(callback_query: types.CallbackQuery, media_type=None, category=None):
    telegram_id = callback_query.from_user.id
    if media_type is None:
        media_type = callback_query.data.split('_')[1]

    update_log_states_data(telegram_id, media_type, 'current_media_type')
    result = await handle_isinstance(callback_query, telegram_id)
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_media', 'current_state')

    if fetch_user_token(telegram_id):
        user_recommendation_data(telegram_id)
        if user_recommendations[telegram_id] == {}:
            rec_list = await handle_media_recommendations(telegram_id, media_type)
            if rec_list:
                # Сохраняем первый media_id (наивысший по рейтингу) как текущий
                update_log_states_data(telegram_id, rec_list[0], 'current_media_id')
                result.current_media_id = rec_list[0]
                # Сохраняем рекомендации в глобальном словаре
                user_recommendations[telegram_id] = rec_list

        if category:
            media = fetch_media_by_id_and_category(category, result.current_media_type, result.current_media_id)
        else:
            media = fetch_media_by_id(result.current_media_type, result.current_media_id)

        markup_inline = InlineKeyboardMarkup()
        markup_inline.row(
            InlineKeyboardButton(result.current_language.previousButton, callback_data='prev_media'),
            InlineKeyboardButton(result.current_language.categoryListButton, callback_data='category'),
            InlineKeyboardButton(result.current_language.nextButton, callback_data='next_media')
        )
        await display_media(callback_query, markup_inline, media)
    else:
        await start(callback_query)

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

async def display_media(entity, markup_inline=None, medias=None):
    telegram_id = entity.from_user.id
    result = await handle_isinstance(entity, telegram_id)

    markup_inline = markup_inline or InlineKeyboardMarkup()
    if medias:
        media = medias[0]
        update_log_states_data(telegram_id, media[0], 'current_media_type_id')
        update_log_states_data(telegram_id, media[2], 'current_media_id')
        if media[5]:
            photo_stream = BytesIO(media[5])
            photo_stream.seek(0)
        else:
            photo_stream = result.current_language.noMediaChooseMedia

        caption = result.current_language.mediaChooseText.format(
            Name=media[3],
            Description=media[4],
            Category=media[6]
        )

        if result.current_state == 'menu_media':
            if verify_user_subscription(telegram_id, media[2]):
                markup_inline.add(InlineKeyboardButton(text=result.current_language.joinButton,
                                                       callback_data=f'subscriptions_list_{result.current_media_type}'))
            else:
                if all(media[i] <= 0 for i in range(8, 13)):
                    markup_inline.add(
                        InlineKeyboardButton(text=result.current_language.joinButton,
                                             callback_data='successful_payment_plan'))
                else:
                    markup_inline.add(
                        InlineKeyboardButton(text=result.current_language.buyButton, callback_data='payment'))
            markup_inline.row(InlineKeyboardButton(text=result.current_language.reportButton, callback_data=f'report'))

        markup_inline.row(InlineKeyboardButton(text=result.current_language.backButton, callback_data='back'))
        if media[5]:
            if result.message_id:
                await bot.edit_message_media(
                    chat_id=result.chat_id,
                    message_id=result.current_message_id,
                    media=types.InputMediaPhoto(photo_stream, caption=caption, parse_mode='HTML'),
                    reply_markup=markup_inline
                )
            else:
                await bot.send_photo(
                    chat_id=result.chat_id,
                    photo=photo_stream,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=markup_inline
                )
        else:
            await edit_entity_message_media(result.chat_id, result.message_id, photo_stream, caption,
                                            current_language=result.current_language,
                                            markup_inline=markup_inline, back_button=True, edit_message=True)
    else:
        message_id = result.current_message_id or result.message_id
        await edit_entity_message_media(result.chat_id, message_id, result.current_language.noMediaChooseMedia,
                                        result.current_language.noMediaChooseText, markup_inline=markup_inline,
                                        current_language=result.current_language,
                                        edit_message=True, back_button=True)

@dp.callback_query_handler(Text(equals='prev_media'))
async def prev_media(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    if fetch_user_token(telegram_id):
        if int(result.current_media_index) > 0:
            new_index = int(result.current_media_index) - 1
            if result.current_state == 'menu_user_media':
                update_log_states_data(telegram_id, new_index, 'current_media_index')
                await user_media_(callback_query, result.current_media_type)
            else:
                rec_list = user_recommendations.get(telegram_id)
                if not rec_list:
                    rec_list = await handle_media_recommendations(telegram_id, result.current_media_type)
                    user_recommendations[telegram_id] = rec_list

                update_log_states_data(telegram_id, rec_list[new_index], 'current_media_id')
                await media_(callback_query, result.current_media_type)
        else:
            await callback_query.answer(result.current_language.startOfListText, show_alert=True)
    else:
        await start(callback_query)

@dp.callback_query_handler(Text(equals='next_media'))
async def next_media(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    if fetch_user_token(telegram_id):
        rec_list = user_recommendations.get(telegram_id)
        if not rec_list:
            rec_list = await handle_media_recommendations(telegram_id, result.current_media_type)
            user_recommendations[telegram_id] = rec_list

        max_index = count_user_media(telegram_id,
                                     result.current_media_type) if result.current_state == 'menu_user_media' else len(
            rec_list)
        if int(result.current_media_index) < max_index - 1:
            new_index = int(result.current_media_index) + 1
            if result.current_state == 'menu_user_media':
                update_log_states_data(telegram_id, new_index, 'current_media_index')
                await user_media_(callback_query, result.current_media_type)
            else:
                update_log_states_data(telegram_id, rec_list[new_index], 'current_media_id')
                await media_(callback_query, result.current_media_type)
        else:
            await callback_query.answer(result.current_language.endOfListText, show_alert=True)
    else:
        await start(callback_query)

@dp.callback_query_handler(Text(equals='delete_media'))
async def delete_media(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    if fetch_user_token(telegram_id):
        delete_user_media(telegram_id, result.current_media_id, result.current_media_type)
        if result.current_state == 'menu_user_media':
            await user_media_(callback_query, result.current_media_type)
        else:
            await media_(callback_query, result.current_media_type)

        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
        caption = result.current_language.deleteMediaText.format(
            media_type=types
        )
        await callback_query.answer(caption, show_alert=True)
    else:
        await start(callback_query)

@dp.callback_query_handler(Text(startswith='create_user_media_'))
async def create_user_media_(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    update_log_states_data(telegram_id, 'menu_user_media', 'current_state')
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    add_media_data(telegram_id)

    if fetch_user_token(telegram_id):
        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType

        user_chats = fetch_user_unregistered_media(telegram_id, result.current_media_type)
        if not user_chats:
            caption = result.current_language.mediaNoChatsText.format (
                media_type= types
            )
            await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addBotMedia,
                                            caption,
                                            current_language=result.current_language, back_button=True,
                                            edit_message=True)
        else:
            buttons = []
            for user_media_id in user_chats:
                chat_info = await bot.get_chat(user_media_id[0])
                title = chat_info.title
                update_log_states_data(telegram_id, user_media_id[0], 'current_media_id')
                buttons.append(InlineKeyboardButton(text=title, callback_data='handle_media_name'))
            markup_inline = InlineKeyboardMarkup(inline_keyboard=[buttons])
            caption = result.current_language.mediaSelectionText.format (
                media_type= types
            )

            await edit_entity_message_media(result.chat_id, result.message_id,
                                            result.current_language.mediaSelectionMedia, caption,
                                            current_language=result.current_language,
                                            markup_inline=markup_inline, back_button=True, edit_message=True)
    else:
        await start(callback_query)

@dp.callback_query_handler(Text(equals='update_user_media_'))
async def update_user_media_(entity):
    telegram_id = entity.from_user.id
    update_log_states_data(telegram_id, 'user_media_', 'current_state')
    result = await handle_isinstance(entity, telegram_id)
    add_media_data(telegram_id)

    if fetch_user_token(telegram_id):
        medias = fetch_user_media(telegram_id, result.current_media_type, result.current_media_id)
        media = medias[0]
        update_log_states_data(telegram_id, media[2], 'current_media_id')
        photo_stream = BytesIO(media[5])
        photo_stream.seek(0)

        markup_inline = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton(text=result.current_language.updateNameButton, callback_data=f'edite_name'),
            InlineKeyboardButton(text=result.current_language.updateDescriptionButton,
                                 callback_data=f'edite_description'),
            InlineKeyboardButton(text=result.current_language.updatePhotoButton, callback_data=f'edite_photo'),
            InlineKeyboardButton(text=result.current_language.updateCategoryButton, callback_data=f'edite_category'),
            InlineKeyboardButton(text=result.current_language.updatePriceButton, callback_data=f'edite_price'),
        )
        markup_inline.row(InlineKeyboardButton(text=result.current_language.backButton, callback_data='back'))
        caption = result.current_language.mediaChooseText.format(
            Name=media[3],
            Description=media[4],
            Category=media[6]
        )
        await bot.edit_message_media(
            chat_id=result.chat_id,
            message_id=result.current_message_id,
            media=types.InputMediaPhoto(photo_stream, caption=caption, parse_mode='HTML'),
            reply_markup=markup_inline
        )
    else:
        await start(entity)

@dp.callback_query_handler(Text(startswith='edite_'))
async def edite_(callback_query: types.CallbackQuery):
    edite_key = callback_query.data.split('_')[1]
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    update_log_states_data(telegram_id, 'update_user_media_', 'current_state')
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')

    if edite_key == 'name':
        await handle_media_name(callback_query)
        return
    elif edite_key == 'description':
        await MediaStates.waiting_for_description.set()
        caption = result.current_language.addDescriptionText
        media_data = result.current_language.addDescriptionMedia
    elif edite_key == 'photo':
        await MediaStates.waiting_for_photo.set()
        caption = result.current_language.addPhotoText
        media_data = result.current_language.addPhotoMedia
    elif edite_key == 'category':
        await handle_media_category(callback_query, 'update_user_media_')
        return
    elif edite_key == 'price':
        await MediaStates.waiting_for_planes.set()
        await handle_media_planes(callback_query)
        return
    else:
        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
        caption = result.current_language.addMediaErrorText.format(media_type=types)
        media_data = result.current_language.errorMedia

    await edit_entity_message_media(result.chat_id, result.message_id, media_data, caption, back_button=True,
                                    edit_message=True, current_language=result.current_language)

@dp.callback_query_handler(Text(equals='handle_media_name'))
async def handle_media_name(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    chat_info = await bot.get_chat(result.current_media_id)
    title = chat_info.title
    if result.current_state == 'menu_user_media':
        update_log_states_data(telegram_id, 'create_user_media_', 'current_state')
        add_media[telegram_id]['media_id'] = result.current_media_id
        add_media[telegram_id]['name'] = title

        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
        caption = result.current_language.addDescriptionText.format(
            media_type=types
        )
        await MediaStates.waiting_for_description.set()
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addDescriptionMedia,
                                        caption, current_language=result.current_language, back_button=True,
                                        edit_message=True)
    if result.current_state == 'update_user_media_':
        update_user_media_data(telegram_id, result.current_media_type_id, result.current_media_type, 'name', title)
        await update_user_media_(callback_query)
        await callback_query.answer('Name changed successfully', show_alert=True)

@dp.message_handler(state=MediaStates.waiting_for_description, content_types=types.ContentType.TEXT)
async def handle_media_description(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    result = await handle_isinstance(message, telegram_id)

    media_type = fetch_log_states_data(telegram_id, 'current_media_type')
    types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
    if not message.text.strip():
        caption = result.current_language.descriptionEmptyErrorText.format(media_type=types)
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia,
                                        caption, current_language=result.current_language,
                                        back_button=True, edit_message=True, delete_message=True,
                                        fixed_message_id=result.current_message_id)
    elif len(message.text) > 250:
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia,
                                        result.current_language.descriptionLengthErrorText,
                                        current_language=result.current_language,
                                        back_button=True, edit_message=True, delete_message=True,
                                        fixed_message_id=result.current_message_id)
    else:
        if result.current_state == 'create_user_media_':
            add_media[telegram_id]['description'] = message.text
            caption = result.current_language.addPhotoText.format(media_type=types)
            await MediaStates.waiting_for_photo.set()
            await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addPhotoMedia,
                                            caption, current_language=result.current_language,
                                            back_button=True, edit_message=True, delete_message=True,
                                            fixed_message_id=result.current_message_id)
        if result.current_state == 'update_user_media_':
            update_user_media_data(telegram_id, result.current_media_type_id, result.current_media_type, 'description',
                                   message.text)
            await bot.delete_message(chat_id=result.chat_id, message_id=message.message_id)
            await update_user_media_(message)
            await state.finish()

@dp.message_handler(state=MediaStates.waiting_for_photo, content_types=types.ContentType.ANY)
async def handle_media_photo(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    result = await handle_isinstance(message, telegram_id)

    if message.photo:
        file_id = message.photo[-1].file_id
        file_info = await bot.get_file(file_id)
        downloaded_file = await bot.download_file(file_info.file_path)

        if result.current_state == 'create_user_media_':
            add_media[telegram_id]['photo'] = downloaded_file.read()
            await MediaStates.waiting_for_planes.set()
            await handle_media_planes(message)

        if result.current_state == 'update_user_media_':
            update_user_media_data(telegram_id, result.current_media_type_id, result.current_media_type, 'photo',
                                   downloaded_file.read())
            await bot.delete_message(chat_id=result.chat_id, message_id=message.message_id)
            await update_user_media_(message)
            await state.finish()

    else:
        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
        caption = result.current_language.invalidPhotoErrorText.format(media_type=types)
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia,
                                        caption, current_language=result.current_language,
                                        back_button=True, edit_message=True, fixed_message_id=result.current_message_id)

@dp.message_handler(state=MediaStates.waiting_for_planes)
async def handle_media_planes(entity):
    telegram_id = entity.from_user.id
    result = await handle_isinstance(entity, telegram_id)

    markup_inline = InlineKeyboardMarkup(row_width=2)
    markup_inline.add(
        InlineKeyboardButton(text=result.current_language.monthPaymentPlanButton, callback_data='handle_plan_price:plan1'),
        InlineKeyboardButton(text=result.current_language.threeMonthPaymentPlanButton, callback_data='handle_plan_price:plan3'),
        InlineKeyboardButton(text=result.current_language.sixMonthPaymentPlanButton, callback_data='handle_plan_price:plan6'),
        InlineKeyboardButton(text=result.current_language.yearPaymentPlanButton, callback_data='handle_plan_price:plan12'),
        InlineKeyboardButton(text=result.current_language.foreverPaymentPlanButton, callback_data='handle_plan_price:plan')
    )

    media_type = fetch_log_states_data(telegram_id, 'current_media_type')
    types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
    caption = result.current_language.addPlanText.format(media_type=types)

    if result.current_state == 'create_user_media_' or result.current_state == 'handle_add_media_planes':
        delete_message = True if not result.current_state == 'handle_add_media_planes' else None
        update_log_states_data(telegram_id, 'create_user_media_', 'current_state')
        markup_inline.add(
            InlineKeyboardButton(text=result.current_language.continueButton, callback_data='handle_plan_price:next'))
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addPlanMedia,
                                        caption, markup_inline=markup_inline, current_language=result.current_language,
                                        delete_message=delete_message, back_button=True, edit_message=True,
                                        fixed_message_id=result.current_message_id)

    if result.current_state == 'update_user_media_' or result.current_state == 'handle_update_media_planes':
        update_log_states_data(telegram_id, 'update_user_media_', 'current_state')
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addPlanMedia,
                                        caption, markup_inline=markup_inline,current_language=result.current_language,
                                        back_button=True, edit_message=True, fixed_message_id=result.current_message_id)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('handle_plan_price:'), state='*')
async def handle_plan_price(callback_query: types.CallbackQuery, state: FSMContext):
    selected = callback_query.data.split(':')[1]
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    if selected == 'next':
        update_log_states_data(telegram_id, 'create_user_media_', 'current_state')
        await state.finish()
        await handle_media_category(callback_query, 'user_media_')
    else:
        if result.current_state == 'create_user_media_':
            update_log_states_data(telegram_id, 'handle_add_media_planes', 'current_state')
        if result.current_state == 'update_user_media_':
            update_log_states_data(telegram_id, 'handle_update_media_planes', 'current_state')
        await state.update_data(selected_plan=selected)
        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
        caption = result.current_language.addPriceText.format(
            media_type=types,
            plan_text=result.current_language.plan_text.get(selected, selected)
        )
        await MediaStates.waiting_for_price.set()
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addPriceMedia, caption,
                                        current_language=result.current_language, back_button=True, edit_message=True)

@dp.message_handler(state=MediaStates.waiting_for_price, content_types=types.ContentType.TEXT)
async def handle_media_price(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    result = await handle_isinstance(message, telegram_id)

    media_type = fetch_log_states_data(telegram_id, 'current_media_type')
    types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
    if not message.text.strip():
        caption = result.current_language.priceEmptyErrorText.format(media_type=types)
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia,
                                        caption, delete_message=True, current_language=result.current_language,
                                        back_button=True, edit_message=True)
    elif not message.text.isdigit():
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia,
                                        result.current_language.invalidPriceErrorText, delete_message=True,
                                        current_language=result.current_language, back_button=True, edit_message=True)
    else:
        data = await state.get_data()
        selected_plan = data.get('selected_plan')

        if result.current_state == 'handle_add_media_planes':
            add_media[telegram_id][f'{selected_plan}_price'] = message.text
        if result.current_state == 'handle_update_media_planes':
            update_user_media_data(telegram_id, result.current_media_type_id, result.current_media_type,
                                   f'{selected_plan}_price', message.text)

        await bot.delete_message(chat_id=result.chat_id, message_id=message.message_id)
        await MediaStates.waiting_for_planes.set()
        await handle_media_planes(message)

@dp.callback_query_handler(Text(equals='category'))
async def category(callback_query: types.CallbackQuery):
    await handle_media_category(callback_query, 'media_')

async def handle_media_category(entity, return_menu=None):
    telegram_id = entity.from_user.id
    result = await handle_isinstance(entity, telegram_id)
    if return_menu:
        update_log_states_data(telegram_id, return_menu, 'current_state')
        update_log_states_data(telegram_id, return_menu, 'temporal_state')

    markup_inline = InlineKeyboardMarkup()
    for index, category in enumerate(result.current_language.categories.keys(), start=1):
        markup_inline.add(InlineKeyboardButton(text=category, callback_data=f'handle_media_subcategory_{index}'))

    media_type = fetch_log_states_data(telegram_id, 'current_media_type')
    types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
    caption = result.current_language.addCategoryText.format(media_type=types)

    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addCategoryMedia, caption, markup_inline=markup_inline,
                                    current_language=result.current_language, back_button=True, edit_message=True)

@dp.callback_query_handler(Text(startswith='handle_media_subcategory_'))
async def handle_media_subcategory_(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    category_index = int(callback_query.data.split('_')[3]) - 1
    category_list = list(result.current_language.categories.keys())
    update_log_states_data(telegram_id, 'handle_media_category', 'current_state')

    if 0 <= category_index < len(category_list):
        selected_category = category_list[category_index]
        add_media[telegram_id]['category'] = selected_category

        markup_inline = InlineKeyboardMarkup(row_width=2)
        for index, subcategory in enumerate(result.current_language.categories[selected_category], start=1):
            markup_inline.add(InlineKeyboardButton(text=subcategory, callback_data=f'handle_media_create_{index}'))

        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
        caption = result.current_language.addSubcategoryText.format(media_type=types)

        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addSubcategoryMedia,
                                        caption, markup_inline=markup_inline, current_language=result.current_language,
                                        back_button=True, edit_message=True)
    else:
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia,
                                        result.current_language.invalidCategoryText,
                                        current_language=result.current_language,
                                        back_button=True, edit_message=True)

@dp.callback_query_handler(Text(startswith='handle_media_create_'))
async def handle_media_create_(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    category = add_media[telegram_id]['category']
    subcategory_index = int(callback_query.data.split('_')[3]) - 1

    if 0 <= subcategory_index < len(result.current_language.categories[category]):
        selected_subcategory = result.current_language.categories[category][subcategory_index]
        if result.temporal_state == 'user_media_':
            add_media[telegram_id]['subcategory'] = selected_subcategory
            user_data = add_media.get(telegram_id)
            create_media(telegram_id, user_data, datetime.now(), result.current_media_type)
            await user_media_(callback_query, result.current_media_type)
            update_log_states_data(telegram_id, None, 'temporal_state')

        elif result.temporal_state == 'media_':
            await media_(callback_query, result.current_media_type, selected_subcategory)
            update_log_states_data(telegram_id, None, 'temporal_state')

        elif result.temporal_state == 'update_user_media_':
            update_user_media_data(telegram_id, result.current_media_type_id, result.current_media_type, 'category',
                                   selected_subcategory)
            await update_user_media_(callback_query)
            update_log_states_data(telegram_id, None, 'temporal_state')
    else:
        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
        caption = result.current_language.addMediaErrorText.format(media_type=types)
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia,
                                        caption, current_language=result.current_language, back_button=True,
                                        edit_message=True)

############################## HANDLE PAYMENT ##############################
@dp.callback_query_handler(Text(equals='payment'))
async def payment(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    update_log_states_data(telegram_id, 'media_', 'current_state')
    price_tuple  = fetch_media_price(result.current_media_id, result.current_media_type)
    tariffs = {
        'plan1': price_tuple[0],
        'plan3': price_tuple[1],
        'plan6': price_tuple[2],
        'plan12': price_tuple[3],
        'plan': price_tuple[4]
    }
    tariffs_buttons = {
        'plan1': result.current_language.monthPaymentPlanButton + f' - ${price_tuple[0]}',
        'plan3': result.current_language.threeMonthPaymentPlanButton + f' - ${price_tuple[1]}',
        'plan6': result.current_language.sixMonthPaymentPlanButton + f' - ${price_tuple[2]}',
        'plan12': result.current_language.yearPaymentPlanButton + f' - ${price_tuple[3]}',
        'plan': result.current_language.foreverPaymentPlanButton + f' - ${price_tuple[4]}'
    }

    if fetch_user_token(telegram_id):
        markup_inline = InlineKeyboardMarkup(row_width=2)
        buttons = [InlineKeyboardButton(text=tariffs_buttons[key], callback_data=f'plan_{key}_{tariffs[key]}')
                   for key, price in tariffs.items() if price > 0]
        markup_inline.add(*buttons)
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.paymentMedia,
                                        result.current_language.paymentPlansText, markup_inline=markup_inline,
                                        current_language=result.current_language,
                                        back_button=True, edit_message=True, fixed_message_id=result.current_message_id)
    else:
        await start(callback_query)

@dp.callback_query_handler(Text(startswith='plan_'))
async def plan_(callback_query: types.CallbackQuery):
    parts = callback_query.data.split('_')
    plan_key, plan_price = parts[1], parts[2]
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    plan = {
        'plan1': result.current_language.monthPaymentPlanButton,
        'plan3': result.current_language.threeMonthPaymentPlanButton,
        'plan6': result.current_language.sixMonthPaymentPlanButton,
        'plan12': result.current_language.yearPaymentPlanButton,
        'plan': result.current_language.foreverPaymentPlanButton
    }

    if fetch_user_token(telegram_id):
        donation_link = await create_donation_link(callback_query, plan_price)
        media_owner_id = fetch_media_owner(result.current_media_id, result.current_media_type)

        if donation_link:
            add_pending_payment(
            buyer_id=telegram_id,
            owner_id=media_owner_id,
            media_id=result.current_media_id,
            media_type=result.current_media_type,
            plan_key=plan_key,
            created_date=datetime.now()
            )

        caption = result.current_language.paymentPlanText.format(
            plan=plan[plan_key],
            price=plan_price
        )

        markup_inline = InlineKeyboardMarkup()
        markup_inline.add(
            InlineKeyboardButton("🔗 ОПЛАТИТЬ", url=donation_link),
            InlineKeyboardButton(text=result.current_language.checkPaymentButton, callback_data=f'check_payment_{plan_key}')
        )
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.paymentMedia,
                                        caption, markup_inline=markup_inline, current_language=result.current_language,
                                        back_button=True, edit_message=True)
        update_log_states_data(telegram_id, f'payment_{result.current_media_id}', 'current_state')
    else:
        await start(callback_query)

@dp.callback_query_handler(Text(startswith='check_payment_'))
async def check_payment_(callback_query: types.CallbackQuery):
    plan_key = callback_query.data.split('_')[2]
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    donation_found = await check_donation_alert(telegram_id, result.current_media_id, result.current_media_type)

    if donation_found:
        await successful_payment_(callback_query, plan_key)
        await callback_query.answer(result.current_language.paymentAcceptedText, show_alert=True)
    else:
        await unsuccessful_payment(callback_query)

@dp.callback_query_handler(Text(equals='create_donation_link'))
async def create_donation_link(entity, amount: float) -> str:
    telegram_id = entity.from_user.id
    result = await handle_isinstance(entity, telegram_id)

    username = None
    access_token = fetch_donation_alerts_token(result.current_media_id, result.current_media_type)
    if not access_token:
        await entity.answer("⚠️ Error: media's owner access token not found", show_alert=True)
        return

    url = "https://www.donationalerts.com/api/v1/user/oauth"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                username = data["data"]["code"]

    if username:
        return f"https://www.donationalerts.com/r/{username}?amount={amount}&message=telegram_id:{telegram_id}"
    else:
        await entity.answer("⚠️ Error: media's owner username not found", show_alert=True)
        return

async def check_donation_alert(telegram_id: int, media_id: int, media_type: str) -> bool:
    access_token = fetch_donation_alerts_token(media_id, media_type)
    if not access_token:
        return False

    url = "https://www.donationalerts.com/api/v1/alerts/donations"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    donations = data.get("data", [])

                    for donation in donations:
                        comment = donation.get("message", "")
                        date = donation.get("created_at")
                        if f"telegram_id:{telegram_id}" in comment:
                            dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
                            if datetime.utcnow() - dt < timedelta(minutes=15):
                                return True
    except Exception as e:
        print(f"Ошибка при проверке доната: {e}")

    return False


@dp.callback_query_handler(Text(startswith='successful_payment_'))
async def successful_payment_(callback_query: types.CallbackQuery, plan_key=None):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    if plan_key is None:
        plan_key = callback_query.data.split('_')[2]

    if result.current_state == 'menu_media' or result.current_state == f'payment_{result.current_media_id}':
        update_log_states_data(telegram_id, 'media_', 'current_state')

    plan = {
        'plan1': 30,
        'plan3': 90,
        'plan6': 180,
        'plan12': 360,
        'plan': None
    }

    if fetch_user_token(telegram_id):
        markup_inline = InlineKeyboardMarkup()
        if plan_key == 'boost':
            expire_date = datetime.now() + timedelta(days=30)
            create_boosts(telegram_id, datetime.now(), expire_date, True)
        else:
            expire_date = datetime.now() + timedelta(days=plan[plan_key]) if plan[plan_key] else None

            link = await bot.create_chat_invite_link(chat_id=result.current_media_id, expire_date=expire_date,
                                                     member_limit=None, creates_join_request=True)
            create_subscription(telegram_id, result.current_media_id, datetime.now(), expire_date, link.invite_link,
                                result.current_media_type)

            markup_inline.add(InlineKeyboardButton(text=result.current_language.subscriptionsButton,
                                                   callback_data=f'subscriptions_list_{result.current_media_type}'))

        media_path = getattr(result.current_language, f'successfulPaymentMedia', None)
        caption = getattr(result.current_language, f'successfulPaymentText', None)

        await edit_entity_message_media(result.chat_id, result.message_id, media_path, caption, markup_inline=markup_inline,
                                        current_language=result.current_language, back_button=True, edit_message=True)
    else:
        await start(callback_query)

@dp.callback_query_handler(Text(equals='unsuccessful_payment'))
async def unsuccessful_payment(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    update_log_states_data(telegram_id, f'payment_{result.current_media_id}', 'current_state')

    if fetch_user_token(telegram_id):
        media_path = getattr(result.current_language, f'unsuccessfulPaymentMedia', None)
        caption = getattr(result.current_language, f'unSuccessfulPaymentText', None)

        markup_inline = InlineKeyboardMarkup()
        markup_inline.add(InlineKeyboardButton(text=result.current_language.supportButton, callback_data='support_user'))
        await edit_entity_message_media(result.chat_id, result.message_id, media_path, caption, markup_inline=markup_inline,
                                        current_language=result.current_language, back_button=True, edit_message=True)
    else:
        await start(callback_query)

############################## HANDLE FUNCTIONS ##############################
@dp.callback_query_handler(Text(equals='back'), state='*')
async def back(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    telegram_id = callback_query.from_user.id
    update_log_states_data(telegram_id, None, 'current_action')
    update_log_states_data(telegram_id, 0, 'current_media_index')
    result = await handle_isinstance(callback_query, telegram_id)

    if result.current_state == 'menu_login':
        await menu_(callback_query, 'login')
    elif result.current_state == 'menu_main':
        await menu_(callback_query, 'main')
    elif result.current_state == 'menu_user':
        await menu_(callback_query, 'user')
    elif result.current_state == 'menu_media':
        await menu_(callback_query, 'media')
    elif result.current_state == 'menu_subscriptions':
        await menu_(callback_query, 'subscriptions')
    elif result.current_state == 'menu_user_media':
        await menu_(callback_query, 'userMedia')
    elif result.current_state == 'user_media_':
        await user_media_(callback_query, result.current_media_type)
    elif result.current_state == 'media_':
        await media_(callback_query, result.current_media_type)
    elif result.current_state == 'update_user_media_':
        await update_user_media_(callback_query)
    elif result.current_state == 'create_user_media_':
        await create_user_media_(callback_query)
    elif result.current_state == 'handle_media_planes':
        await handle_media_planes(callback_query)
    elif result.current_state == 'handle_media_category':
        await handle_media_category(callback_query, result.temporal_state)
    elif result.current_state == 'handle_update_media_planes':
        await MediaStates.waiting_for_planes.set()
        await handle_media_planes(callback_query)
    elif result.current_state == 'handle_add_media_planes':
        await MediaStates.waiting_for_planes.set()
        await handle_media_planes(callback_query)

    elif result.current_state == f'payment_{result.current_media_id}':
        callback_query.data = f'payment_{result.current_media_id}'
        await payment(callback_query)
    elif result.current_state == f'plan_{result.current_media_id}':
        callback_query.data = f'plan_{result.current_media_id}'
        await plan_(callback_query)
    elif result.current_state == f'unsuccessful_payment_{result.current_media_id}':
        callback_query.data = f'unsuccessful_payment_{result.current_media_id}'
        await unsuccessful_payment(callback_query)

@dp.chat_join_request_handler()
async def handle_join_request(event: types.ChatJoinRequest):
    telegram_id = event.from_user.id
    media_id = event.chat.id
    if verify_user_subscription(telegram_id, media_id):
        await bot.approve_chat_join_request(chat_id=media_id, user_id=telegram_id)
    else:
        await bot.decline_chat_join_request(chat_id=media_id, user_id=telegram_id)

@dp.my_chat_member_handler()
async def my_chat_member_handler(update: types.ChatMemberUpdated):
    # Note that in some cases, the initiator may not be the owner of the chat.
    owner_id = update.from_user.id
    media_id = update.chat.id
    new_status = update.new_chat_member.status
    old_status = update.old_chat_member.status

    if update.new_chat_member.user.id != bot.id:
        return
    if new_status == old_status:
        return

    chat_type_value = update.chat.type
    if chat_type_value == 'channel':
        media_type = 'channel'
    elif chat_type_value in ['group', 'supergroup']:
        media_type = 'group'
    else:
        media_type = chat_type_value

    record = verify_log_media(media_id)
    try:
        if new_status in ['administrator', 'creator']:
            if record is None:
                create_log_media(owner_id, media_id, new_status, media_type, datetime.now(), datetime.now())
            else:
                update_log_media_status(new_status, owner_id, media_type, media_id, datetime.now())
        else:
            update_log_media_status(new_status, None, media_type, media_id, datetime.now()) if record else None
    except Exception as e:
        db_connection.rollback()
        print(f'# Error while updating status for the chat {media_id}: {e}')

async def vinculate_DA(telegram_id):
    query = urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "oauth-user-show oauth-donation-index",
        "state": f"telegram_id:{telegram_id}"
    })
    auth_url = f"https://www.donationalerts.com/oauth/authorize?{query}"
    return auth_url

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

async def handle_expired_subscriptions():
    while True:
        await cursor.execute('SELECT buyer_id, group_id FROM subscriptions WHERE expire_date <= %s', (datetime.now(),))
        expired_subscriptions = await cursor.fetchall()

        for buyer_id, group_id in expired_subscriptions:
            try:
                await bot.kick_chat_member(chat_id=group_id, user_id=buyer_id)
            except Exception as e:
                print(f'Error removing user {buyer_id} from group {group_id}: {e}')

            await cursor.execute('DELETE FROM subscriptions WHERE buyer_id = %s AND group_id = %s',
                                 (buyer_id, group_id))
        await db_connection.commit()
        await asyncio.sleep(3600)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    loop = asyncio.get_event_loop()
    loop.create_task(handle_expired_subscriptions())
