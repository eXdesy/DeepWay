# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
import asyncio
from aiogram import types
from datetime import datetime
from aiogram.utils import executor

from configs import bot, dp
from handlers.sql_handler import cursor, db_connection, verify_user_subscription, verify_log_media, create_log_media, update_log_media_status

import bot_handlers.login_handler
import bot_handlers.media_handler
import bot_handlers.payment_handler

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
