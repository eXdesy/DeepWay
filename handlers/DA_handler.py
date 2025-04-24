# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
import os
import aiohttp
from dotenv import load_dotenv
from urllib.parse import urlencode
from datetime import datetime, timedelta
from handlers.sql_handler import fetch_donation_alerts_token

load_dotenv()
CLIENT_ID = os.getenv("DONATIONALERTS_CLIENT_ID")
CLIENT_SECRET = os.getenv("DONATIONALERTS_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


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


async def create_donation_link(entity, telegram_id: int, amount: float, media_id: int, media_type: str) -> str:
    username = None
    access_token = fetch_donation_alerts_token(media_id, media_type)
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
