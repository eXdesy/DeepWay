# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
from io import BytesIO
from aiogram import types
from datetime import datetime
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from configs import dp, bot
from handlers.sql_handler import *
from handlers.localdata_handler import handle_isinstance, user_recommendation_data, user_recommendations, MediaStates, add_media, add_media_data, handle_media_recommendations, edit_entity_message_media


@dp.callback_query_handler(Text(startswith='user_media_'))
async def user_media_(callback_query: types.CallbackQuery, media_type=None):
    telegram_id = callback_query.from_user.id
    if media_type is None:
        media_type = callback_query.data.split('_')[2]

    update_log_states_data(telegram_id, media_type, 'current_media_type')
    result = await handle_isinstance(callback_query, telegram_id)
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

    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_user_media', 'current_state')
    await display_media(callback_query, markup_inline, media)


@dp.callback_query_handler(Text(startswith='media_'))
async def media_(callback_query: types.CallbackQuery, media_type=None, category=None):
    telegram_id = callback_query.from_user.id
    if media_type is None:
        media_type = callback_query.data.split('_')[1]

    update_log_states_data(telegram_id, media_type, 'current_media_type')
    result = await handle_isinstance(callback_query, telegram_id)

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
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    update_log_states_data(telegram_id, 'menu_media', 'current_state')
    await display_media(callback_query, markup_inline, media)


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
                                            markup_inline=markup_inline, current_language=result.current_language,
                                            delete_message=None, back_button=True, edit_message=True,
                                            fixed_message_id=None)
    else:
        message_id = result.current_message_id or result.message_id
        await edit_entity_message_media(result.chat_id, message_id, result.current_language.noMediaChooseMedia,
                                        result.current_language.noMediaChooseText, markup_inline=markup_inline,
                                        current_language=result.current_language, delete_message=None, back_button=True,
                                        edit_message=True, fixed_message_id=None)


@dp.callback_query_handler(Text(equals='prev_media'))
async def prev_media(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

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


@dp.callback_query_handler(Text(equals='next_media'))
async def next_media(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    rec_list = user_recommendations.get(telegram_id)
    if not rec_list:
        rec_list = await handle_media_recommendations(telegram_id, result.current_media_type)
        user_recommendations[telegram_id] = rec_list

    max_index = count_user_media(telegram_id, result.current_media_type) if result.current_state == 'menu_user_media' else len(rec_list)
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


@dp.callback_query_handler(Text(equals='delete_media'))
async def delete_media(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    delete_user_media(telegram_id, result.current_media_id, result.current_media_type)
    if result.current_state == 'menu_user_media':
        await user_media_(callback_query, result.current_media_type)
    else:
        await media_(callback_query, result.current_media_type)

    media_type = fetch_log_states_data(telegram_id, 'current_media_type')
    types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
    caption = result.current_language.deleteMediaText.format(media_type=types)
    await callback_query.answer(caption, show_alert=True)


@dp.callback_query_handler(Text(startswith='create_user_media_'))
async def create_user_media_(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)
    add_media_data(telegram_id)

    media_type = fetch_log_states_data(telegram_id, 'current_media_type')
    types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
    update_log_states_data(telegram_id, 'menu_user_media', 'current_state')
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')

    user_chats = fetch_user_unregistered_media(telegram_id, result.current_media_type)
    if not user_chats:
        caption = result.current_language.mediaNoChatsText.format(media_type=types)
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addBotMedia,
                                        caption, markup_inline=None, current_language=result.current_language,
                                        delete_message=None, back_button=True, edit_message=True, fixed_message_id=None)

    else:
        buttons = []
        for user_media_id in user_chats:
            chat_info = await bot.get_chat(user_media_id[0])
            title = chat_info.title
            update_log_states_data(telegram_id, user_media_id[0], 'current_media_id')
            buttons.append(InlineKeyboardButton(text=title, callback_data='handle_media_name'))
        markup_inline = InlineKeyboardMarkup(inline_keyboard=[buttons])
        caption = result.current_language.mediaSelectionText.format(media_type=types)

        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.mediaSelectionMedia,
                                        caption, markup_inline=markup_inline, current_language=result.current_language,
                                        delete_message=None, back_button=True, edit_message=True, fixed_message_id=None)


@dp.callback_query_handler(Text(equals='update_user_media_'))
async def update_user_media_(entity):
    telegram_id = entity.from_user.id
    result = await handle_isinstance(entity, telegram_id)
    add_media_data(telegram_id)

    medias = fetch_user_media(telegram_id, result.current_media_type, result.current_media_id)
    media = medias[0]
    photo_stream = BytesIO(media[5])
    photo_stream.seek(0)

    markup_inline = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(text=result.current_language.updateNameButton, callback_data=f'edite_name'),
        InlineKeyboardButton(text=result.current_language.updateDescriptionButton, callback_data=f'edite_description'),
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
    update_log_states_data(telegram_id, 'user_media_', 'current_state')
    update_log_states_data(telegram_id, media[2], 'current_media_id')

    await bot.edit_message_media(
        chat_id=result.chat_id,
        message_id=result.current_message_id,
        media=types.InputMediaPhoto(photo_stream, caption=caption, parse_mode='HTML'),
        reply_markup=markup_inline
    )


@dp.callback_query_handler(Text(startswith='edite_'))
async def edite_(callback_query: types.CallbackQuery):
    edite_key = callback_query.data.split('_')[1]
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

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

    update_log_states_data(telegram_id, 'update_user_media_', 'current_state')
    update_log_states_data(telegram_id, result.message_id, 'current_message_id')
    await edit_entity_message_media(result.chat_id, result.message_id, media_data, caption, markup_inline=None,
                                    current_language=result.current_language, delete_message=True, back_button=True,
                                    edit_message=True, fixed_message_id=None)


@dp.callback_query_handler(Text(equals='handle_media_name'))
async def handle_media_name(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    chat_info = await bot.get_chat(result.current_media_id)
    title = chat_info.title
    if result.current_state == 'menu_user_media':
        add_media[telegram_id]['media_id'] = result.current_media_id
        add_media[telegram_id]['name'] = title

        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
        caption = result.current_language.addDescriptionText.format(
            media_type=types
        )
        await MediaStates.waiting_for_description.set()
        update_log_states_data(telegram_id, 'create_user_media_', 'current_state')
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addDescriptionMedia,
                                        caption, markup_inline=None, current_language=result.current_language,
                                        delete_message=None, back_button=True, edit_message=True,
                                        fixed_message_id=None)

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
                                        caption, markup_inline=None, current_language=result.current_language,
                                        delete_message=True, back_button=True, edit_message=True,
                                        fixed_message_id=result.current_message_id)
    elif len(message.text) > 250:
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia,
                                        result.current_language.descriptionLengthErrorText, markup_inline=None,
                                        current_language=result.current_language, delete_message=True, back_button=True,
                                        edit_message=True, fixed_message_id=result.current_message_id)
    else:
        if result.current_state == 'create_user_media_':
            add_media[telegram_id]['description'] = message.text
            caption = result.current_language.addPhotoText.format(media_type=types)
            await MediaStates.waiting_for_photo.set()
            await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addPhotoMedia,
                                            caption, markup_inline=None, current_language=result.current_language,
                                            delete_message=True, back_button=True, edit_message=True,
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
                                        caption, markup_inline=None, current_language=result.current_language,
                                        delete_message=True, back_button=True, edit_message=True,
                                        fixed_message_id=result.current_message_id)


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
        markup_inline.add(
            InlineKeyboardButton(text=result.current_language.continueButton, callback_data='handle_plan_price:next'))
        update_log_states_data(telegram_id, 'create_user_media_', 'current_state')
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addPlanMedia,
                                        caption, markup_inline=markup_inline, current_language=result.current_language,
                                        delete_message=delete_message, back_button=True, edit_message=True,
                                        fixed_message_id=result.current_message_id)

    if result.current_state == 'update_user_media_' or result.current_state == 'handle_update_media_planes':
        update_log_states_data(telegram_id, 'update_user_media_', 'current_state')
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addPlanMedia,
                                        caption, markup_inline=markup_inline, current_language=result.current_language,
                                        delete_message=None, back_button=True, edit_message=True,
                                        fixed_message_id=result.current_message_id)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('handle_plan_price:'), state='*')
async def handle_plan_price(callback_query: types.CallbackQuery, state: FSMContext):
    selected = callback_query.data.split(':')[1]
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    if selected == 'next':
        await state.finish()
        update_log_states_data(telegram_id, 'create_user_media_', 'current_state')
        await handle_media_category(callback_query, 'user_media_')
    else:
        await state.update_data(selected_plan=selected)
        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
        caption = result.current_language.addPriceText.format(
            media_type=types,
            plan_text=result.current_language.plan_text.get(selected, selected)
        )
        await MediaStates.waiting_for_price.set()
        if result.current_state == 'create_user_media_':
            update_log_states_data(telegram_id, 'handle_add_media_planes', 'current_state')
        if result.current_state == 'update_user_media_':
            update_log_states_data(telegram_id, 'handle_update_media_planes', 'current_state')
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addPriceMedia,
                                        caption, markup_inline=None, current_language=result.current_language,
                                        delete_message=None, back_button=True, edit_message=True, fixed_message_id=None)


@dp.message_handler(state=MediaStates.waiting_for_price, content_types=types.ContentType.TEXT)
async def handle_media_price(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    result = await handle_isinstance(message, telegram_id)

    media_type = fetch_log_states_data(telegram_id, 'current_media_type')
    types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
    if not message.text.strip():
        caption = result.current_language.priceEmptyErrorText.format(media_type=types)
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia,
                                        caption, markup_inline=None, current_language=result.current_language,
                                        delete_message=True, back_button=True, edit_message=True,
                                        fixed_message_id=result.current_message_id)
    elif not message.text.isdigit():
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia,
                                        result.current_language.invalidPriceErrorText, markup_inline=None,
                                        current_language=result.current_language, delete_message=True, back_button=True,
                                        edit_message=True, fixed_message_id=result.current_message_id)
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

    markup_inline = InlineKeyboardMarkup()
    for index, category in enumerate(result.current_language.categories.keys(), start=1):
        markup_inline.add(InlineKeyboardButton(text=category, callback_data=f'handle_media_subcategory_{index}'))

    media_type = fetch_log_states_data(telegram_id, 'current_media_type')
    types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
    caption = result.current_language.addCategoryText.format(media_type=types)
    if return_menu:
        update_log_states_data(telegram_id, return_menu, 'current_state')
        update_log_states_data(telegram_id, return_menu, 'temporal_state')

    await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.addCategoryMedia,
                                    caption, markup_inline=markup_inline, current_language=result.current_language,
                                    delete_message=None, back_button=True, edit_message=True, fixed_message_id=None)


@dp.callback_query_handler(Text(startswith='handle_media_subcategory_'))
async def handle_media_subcategory_(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    result = await handle_isinstance(callback_query, telegram_id)

    category_index = int(callback_query.data.split('_')[3]) - 1
    category_list = list(result.current_language.categories.keys())

    add_media_data(telegram_id)
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
                                        delete_message=None, back_button=True, edit_message=True, fixed_message_id=None)
    else:
        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia,
                                        result.current_language.invalidCategoryText, markup_inline=None,
                                        current_language=result.current_language, delete_message=None, back_button=True,
                                        edit_message=True, fixed_message_id=None)


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
            update_log_states_data(telegram_id, None, 'temporal_state')
            await user_media_(callback_query, result.current_media_type)

        elif result.temporal_state == 'media_':
            update_log_states_data(telegram_id, None, 'temporal_state')
            await media_(callback_query, result.current_media_type, selected_subcategory)

        elif result.temporal_state == 'update_user_media_':
            update_user_media_data(telegram_id, result.current_media_type_id, result.current_media_type, 'category',
                                   selected_subcategory)
            update_log_states_data(telegram_id, None, 'temporal_state')
            await update_user_media_(callback_query)
    else:
        media_type = fetch_log_states_data(telegram_id, 'current_media_type')
        types = result.current_language.channelType if media_type == 'channels' else result.current_language.groupType
        caption = result.current_language.addMediaErrorText.format(media_type=types)

        await edit_entity_message_media(result.chat_id, result.message_id, result.current_language.errorMedia, caption,
                                        markup_inline=None, current_language=result.current_language, delete_message=None,
                                        back_button=True, edit_message=True, fixed_message_id=None)
