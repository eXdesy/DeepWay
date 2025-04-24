# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
import os
import aiohttp
from aiogram import types
from fastapi import FastAPI, Request

from bot_handlers.payment_handler import successful_payment_, unsuccessful_payment
from handlers.sql_handler import update_user_data, cursor, db_connection

app = FastAPI()

CLIENT_ID = os.getenv("DONATIONALERTS_CLIENT_ID")
CLIENT_SECRET = os.getenv("DONATIONALERTS_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

@app.get("/callback")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code or not state:
        return {"error": "Missing parameters"}

    telegram_id = int(state.split(":")[1])

    async with aiohttp.ClientSession() as session:
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }
        async with session.post("https://www.donationalerts.com/oauth/token", data=data) as resp:
            result = await resp.json()
            access_token = result.get("access_token")
            if not access_token:
                return {"error": "Failed to get access token"}

            update_user_data(telegram_id, access_token, "donation_alerts_token")
            return {"status": "Access token saved! You can return to Telegram now."}

@app.post("/donation")
async def receive_donation(request: Request):
    data = await request.json()
    message = data.get("message", "")

    if "telegram_id:" not in message:
        return {"status": "ignored"}

    buyer_id = int(message.split("telegram_id:")[1].strip())

    # Создаём фейковый callback_query
    callback_query = types.CallbackQuery(
        id="webhook",
        from_user=types.User(id=buyer_id, is_bot=False),
        message=None,
        data=""
    )

    try:
        # Получаем ожидаемую оплату
        cursor.execute(
            "SELECT plan_key, media_id, media_type, owner_id FROM payments WHERE buyer_id = %s ORDER BY created_at DESC LIMIT 1",
            (buyer_id,)
        )
        row = cursor.fetchone()
        if not row:
            return {"status": "no pending payment"}

        plan_key, media_id, media_type, owner_id = row

        # Вызываем success
        await successful_payment_(callback_query, plan_key)

        # Удаляем выполненное ожидание
        cursor.execute("DELETE FROM payments WHERE buyer_id = %s", (buyer_id,))
        db_connection.commit()

        return {"status": "success"}
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        try:
            await unsuccessful_payment(callback_query)
        except:
            pass
        return {"status": "fail"}

