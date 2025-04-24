# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
from aiogram import types
from datetime import datetime, timedelta
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from configs import dp, bot
from handlers.sql_handler import *
from handlers.localdata_handler import handle_isinstance, update_log_states_data, edit_entity_message_media
from handlers.DA_handler import create_donation_link, check_donation_alert


@dp.callback_query_handler(Text(equals='payment'))
async def payment(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
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

    markup_inline = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text=tariffs_buttons[key], callback_data=f'plan_{key}_{tariffs[key]}')
               for key, price in tariffs.items() if price > 0]
    markup_inline.add(*buttons)

    update_log_states_data(telegram_id, 'media_', 'current_state')
    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.paymentMedia,
                                    result.current_language.paymentPlansText, markup_inline=markup_inline,
                                    current_language=result.current_language, delete_message=None, back_button=True,
                                    edit_message=True, fixed_message_id=result.current_message_id)


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

    donation_link = await create_donation_link(callback_query, telegram_id, plan_price, result.current_media_id,
                                               result.current_media_type)
    media_owner_id = fetch_media_owner(result.current_media_id, result.current_media_type)

    if donation_link:
        add_pending_payment(
            buyer_id=telegram_id,
            owner_id=media_owner_id[0],
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
        InlineKeyboardButton(text="🔗 ОПЛАТИТЬ", url=donation_link),
        InlineKeyboardButton(text=result.current_language.checkPaymentButton, callback_data=f'check_payment_{plan_key}')
    )
    update_log_states_data(telegram_id, f'payment_{result.current_media_id}', 'current_state')
    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.paymentMedia,
                                    caption, markup_inline=markup_inline, current_language=result.current_language,
                                    delete_message=None, back_button=True, edit_message=True, fixed_message_id=None)


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


@dp.callback_query_handler(Text(startswith='successful_payment_'))
async def successful_payment_(callback_query: types.CallbackQuery, plan_key=None):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    if plan_key is None:
        plan_key = callback_query.data.split('_')[2]

    plan = {
        'plan1': 30,
        'plan3': 90,
        'plan6': 180,
        'plan12': 360,
        'plan': None
    }

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
    if result.current_state == 'menu_media' or result.current_state == f'payment_{result.current_media_id}':
        update_log_states_data(telegram_id, 'media_', 'current_state')

    await edit_entity_message_media(result.chat_id, result.message_id, media_path, caption, markup_inline=markup_inline,
                                    current_language=result.current_language, delete_message=None, back_button=True,
                                    edit_message=True, fixed_message_id=None)


@dp.callback_query_handler(Text(equals='unsuccessful_payment'))
async def unsuccessful_payment(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    media_path = getattr(result.current_language, f'unsuccessfulPaymentMedia', None)
    caption = getattr(result.current_language, f'unSuccessfulPaymentText', None)

    markup_inline = InlineKeyboardMarkup()
    markup_inline.add(InlineKeyboardButton(text=result.current_language.supportButton, callback_data='support_user'))

    update_log_states_data(telegram_id, f'payment_{result.current_media_id}', 'current_state')
    await edit_entity_message_media(result.chat_id, result.message_id, media_path, caption, markup_inline=markup_inline,
                                    current_language=result.current_language, delete_message=None, back_button=True,
                                    edit_message=True, fixed_message_id=None)

