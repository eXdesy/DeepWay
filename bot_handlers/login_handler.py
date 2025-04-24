# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
from aiogram import types
from datetime import datetime
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from configs import dp, bot
from handlers.sql_handler import *
from handlers.token_handler import *
from handlers.DA_handler import vinculate_DA
from bot_handlers.payment_handler import payment, plan_, unsuccessful_payment
from handlers.localdata_handler import edit_entity_message_media, handle_isinstance, MediaStates
from bot_handlers.media_handler import user_media_, media_, update_user_media_, create_user_media_, handle_media_category, handle_media_planes


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
        media_data = result.current_language.loginMenuMedia
        caption = result.current_language.loginMenuText

        markup_inline.add(
            InlineKeyboardButton(text=result.current_language.loginButton, callback_data='login'),
            InlineKeyboardButton(text=result.current_language.restoreAccountButton, callback_data='restore_account'),
            InlineKeyboardButton(text=result.current_language.supportButton, callback_data='support_')
        )
        update_log_states_data(telegram_id, 'login', 'current_state')

    elif menu_type == 'main' and fetch_user_token(telegram_id):
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
        update_log_states_data(telegram_id, 'main', 'current_state')

    elif menu_type == 'language':
        media_data = r'media\language.png'
        caption = (
            '🇺🇸 Choose your the language\n'
            '🇷🇺 Выберите свой язык\n'
            '🇪🇸 Elige tu idioma\n'
            '🇺🇦 Оберіть свою мову\n\n'
            '💡 You can change the language anytime in the settings.'
        )

        markup_inline.add(
            InlineKeyboardButton(text='ENGLISH 🇺🇸', callback_data='language_us'),
            InlineKeyboardButton(text='РУССКИЙ 🇷🇺', callback_data='language_ru'),
            InlineKeyboardButton(text='ESPAÑOL 🇪🇸', callback_data='language_es'),
            InlineKeyboardButton(text='УКРАЇНСЬКА 🇺🇦', callback_data='language_uk')
        )

        if result.not_callback is None:
            fixed_message_id = result.message_id
            current_language = result.current_language
            back_button = True
            update_log_states_data(telegram_id, 'menu_user', 'current_state')

    elif menu_type == 'user' and fetch_user_token(telegram_id):
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
        update_log_states_data(telegram_id, 'menu_main', 'current_state')

    elif menu_type == 'media' and fetch_user_token(telegram_id):
        media_data = result.current_language.mediaMenuMedia
        caption = result.current_language.mediaMenuText
        current_language = result.current_language
        back_button = True

        markup_inline.add(
            InlineKeyboardButton(text=result.current_language.channelsButton, callback_data='media_channels'),
            InlineKeyboardButton(text=result.current_language.groupsButton, callback_data='media_groups')
        )
        update_log_states_data(telegram_id, 'menu_main', 'current_state')

    elif menu_type == 'userMedia' and fetch_user_token(telegram_id):
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
        update_log_states_data(telegram_id, 'menu_user', 'current_state')

    elif menu_type == 'subscriptions' and fetch_user_token(telegram_id):
        media_data = result.current_language.subscriptionsMenuMedia
        caption = result.current_language.subscriptionsMenuText
        current_language = result.current_language
        back_button = True

        markup_inline.add(
            InlineKeyboardButton(text=result.current_language.channelsButton,
                                 callback_data='subscriptions_list_channels'),
            InlineKeyboardButton(text=result.current_language.groupsButton, callback_data='subscriptions_list_groups')
        )
        update_log_states_data(telegram_id, 'menu_user', 'current_state')

    else:
        await start(entity)

    await edit_entity_message_media(result.chat_id, result.message_id, media_data, caption, markup_inline=markup_inline,
                                    current_language=current_language, delete_message=delete_message,
                                    back_button=back_button, edit_message=edit_message, fixed_message_id=fixed_message_id)


@dp.callback_query_handler(Text(equals='boost'))
async def boost(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    markup_inline = InlineKeyboardMarkup()
    markup_inline.row(
        InlineKeyboardButton(text=result.current_language.checkPaymentButton, callback_data=f'check_payment_boost'))

    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_user_media', 'current_state')
    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.boostMedia,
                                    result.current_language.boostText, markup_inline=None,
                                    current_language=result.current_language, delete_message=None, back_button=True,
                                    edit_message=True, fixed_message_id=None)


@dp.callback_query_handler(Text(startswith='support_'))
async def support_(callback_query: types.CallbackQuery):
    action = callback_query.data.split('_')[1]
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'support', 'temporal_state')
    update_log_states_data(telegram_id, 'menu_main', 'current_state') if action == 'user' \
        else update_log_states_data(telegram_id, 'menu_login', 'current_state')
    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.supportMedia,
                                    result.current_language.supportText, markup_inline=None,
                                    current_language=result.current_language, delete_message=None, back_button=True,
                                    edit_message=True, fixed_message_id=None)



@dp.callback_query_handler(Text(equals='report'))
async def report(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    media_id = fetch_log_states_data(telegram_id, 'current_media_id')
    media_type = fetch_log_states_data(telegram_id, 'current_media_type')

    types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
    chat_info = await bot.get_chat(media_id)
    title = chat_info.title

    caption = result.current_language.reportText.format(
        channel_name=title,
        media_type=types
    )

    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'media_', 'current_state')
    update_log_states_data(telegram_id, 'report', 'temporal_state')
    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.reportMedia,
                                    caption, markup_inline=None, current_language=result.current_language,
                                    delete_message=None, back_button=True, edit_message=True, fixed_message_id=None)


@dp.callback_query_handler(Text(equals='restore_account'))
async def restore_account(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_login', 'current_state')
    update_log_states_data(telegram_id, 'restore_account', 'temporal_state')
    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.restoreAccountMedia,
                                    result.current_language.restoreAccountText, markup_inline=None,
                                    current_language=result.current_language, delete_message=None, back_button=True,
                                    edit_message=True, fixed_message_id=None)


@dp.callback_query_handler(Text(equals='password'))
async def password(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_user', 'current_state')
    update_log_states_data(telegram_id, 'validate_user_password', 'temporal_state')
    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.passwordMedia,
                                    result.current_language.updatePasswordText, markup_inline=None,
                                    current_language=result.current_language, delete_message=None, back_button=True,
                                    edit_message=True, fixed_message_id=None)


@dp.callback_query_handler(Text(equals='login'))
async def login(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    username = callback_query.from_user.username
    result = await handle_isinstance(callback_query, telegram_id)

    if verify_user(telegram_id):
        menuMedia = result.current_language.loginMedia
        if verify_user_data(telegram_id, username, 'username'):

            caption = result.current_language.loginText
            update_log_states_data(telegram_id, username, 'current_action')
            update_log_states_data(telegram_id, 'login', 'temporal_state')
        else:
            caption = result.current_language.usernameErrorText
            update_log_states_data(telegram_id, 'update_username', 'temporal_state')
    else:
        menuMedia = result.current_language.registerMedia
        if username:
            caption = result.current_language.registerText
            update_log_states_data(telegram_id, 'register', 'temporal_state')
            update_log_states_data(telegram_id, username, 'current_action')
        else:
            caption = result.current_language.usernameErrorText

    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_login', 'current_state')
    await edit_entity_message_media(result.chat_id, result.message_id, menuMedia, caption, markup_inline=None,
                                    current_language=result.current_language, delete_message=None, back_button=True,
                                    edit_message=True, fixed_message_id=None)


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

    if result.current_state == 'menu_media':
        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
        caption = result.current_language.alreadyJoinedText.format(media_type=types)
        await entity.answer(caption, show_alert=True)
        update_log_states_data(telegram_id, 'media_', 'current_state')
    if result.current_state == 'media_':
        update_log_states_data(telegram_id, 'media_', 'current_state')

    caption = result.current_language.subscriptionTitleText
    subscriptions = fetch_user_subscriptions(telegram_id, media_type)
    markup_inline = InlineKeyboardMarkup(row_width=2)
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

    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_subscriptions', 'current_state')

    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.subscriptionsMenuMedia,
                                    caption, markup_inline=markup_inline, current_language=result.current_language,
                                    delete_message=None, back_button=True, edit_message=True, fixed_message_id=None)



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

    await edit_entity_message_media(result.chat_id, result.message_id, media_data, caption, markup_inline=None,
                                    current_language=result.current_language, delete_message=True, back_button=True,
                                    edit_message=True, fixed_message_id=result.current_message_id)


############################## HANDLE FUNCTIONS ##############################
@dp.callback_query_handler(Text(equals='back'), state='*')
async def back(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    telegram_id = callback_query.from_user.id
    update_log_states_data(telegram_id, None, 'current_action')
    update_log_states_data(telegram_id, None, 'temporal_state')
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
