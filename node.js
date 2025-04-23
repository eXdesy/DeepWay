require("dotenv").config();
const { ApiClient } = require("@donation-alerts/api");
const axios = require("axios");

// Токен владельца аккаунта Donation Alerts
const accessToken = process.env.ACCESS_TOKEN;

// Адрес, куда слать донаты
const webhook = process.env.TELEGRAM_WEBHOOK;

const da = new ApiClient({ accessToken });

da.connect();

da.on("donation", async (donation) => {
  console.log("🎉 Новый донат:", donation);

  const payload = {
    username: donation.username,
    amount: donation.amount,
    message: donation.message,
    created_at: donation.created_at
  };

  try {
    const res = await axios.post(webhook, payload);
    console.log("✅ Отправлено в FastAPI:", res.data);
  } catch (err) {
    console.error("❌ Ошибка при отправке:", err.message);
  }
});

da.on("connect", () => console.log("🔗 Успешно подключено к Donation Alerts через WebSocket"));
da.on("error", (err) => console.error("🚨 Ошибка подключения:", err.message));
