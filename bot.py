import csv
import io
import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List

import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

DEFAULT_ADMIN_USERNAMES = {"cloudmanagerss"}


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    price: int
    category: str


CATALOG: Dict[str, List[Product]] = {
    "liquids": [
        Product("liq-001", "Жижа Mango Ice 30ml", 650, "Жижи"),
        Product("liq-002", "Жижа Berry Mix 30ml", 620, "Жижи"),
        Product("liq-003", "Жижа Cola Lime 30ml", 600, "Жижи"),
    ],
    "devices": [
        Product("dev-001", "Vape Pod A1", 2400, "Электронные сигареты"),
        Product("dev-002", "Vape Pod Mini X", 2900, "Электронные сигареты"),
    ],
    "cartridges": [
        Product("cart-001", "Картридж 1.0Ω", 350, "Картриджи"),
        Product("cart-002", "Картридж 0.8Ω", 390, "Картриджи"),
    ],
}

CATEGORY_LABELS = {
    "liquids": "🧪 Жижи",
    "devices": "💨 Электронные сигареты",
    "cartridges": "🧩 Картриджи",
    "other": "📦 Остальное",
}

PRODUCTS_BY_SKU: Dict[str, Product] = {}


def build_product_index() -> None:
    PRODUCTS_BY_SKU.clear()
    for products in CATALOG.values():
        for product in products:
            PRODUCTS_BY_SKU[product.sku] = product


def apply_markup(cost: float) -> int:
    if cost <= 200:
        return int(round(cost * 1.80))
    if cost <= 250:
        return int(round(cost * 1.50))
    return int(round(cost * 1.35))


def normalize_category(name: str) -> str:
    low = (name or "").lower()
    if any(x in low for x in ["жиж", "liquid"]):
        return "liquids"
    if any(x in low for x in ["сигар", "pod", "device", "однораз"]):
        return "devices"
    if any(x in low for x in ["картрид", "cartridge", "coil"]):
        return "cartridges"
    return "other"


def fetch_price_rows() -> List[dict]:
    source = os.getenv("PRICE_SOURCE", "")
    if not source:
        return []

    if source.startswith("http://") or source.startswith("https://"):
        response = requests.get(source, timeout=20)
        response.raise_for_status()
        raw = response.text
    else:
        with open(source, "r", encoding="utf-8") as f:
            raw = f.read()

    rows: List[dict] = []
    if source.endswith(".json"):
        data = json.loads(raw)
        if isinstance(data, dict):
            data = data.get("rows", [])
        for item in data:
            if isinstance(item, dict):
                rows.append(item)
        return rows

    reader = csv.DictReader(io.StringIO(raw))
    for row in reader:
        rows.append(row)
    return rows


def load_catalog_from_price_source() -> bool:
    rows = fetch_price_rows()
    if not rows:
        return False

    new_catalog: Dict[str, List[Product]] = {k: [] for k in CATEGORY_LABELS}
    for i, row in enumerate(rows, start=1):
        name = (row.get("name") or row.get("Наименование") or "").strip()
        if not name:
            continue

        cost_raw = (
            row.get("purchase_price")
            or row.get("cost")
            or row.get("Закуп")
            or row.get("Цена")
            or ""
        )
        try:
            cost = float(str(cost_raw).replace(" ", "").replace(",", "."))
        except ValueError:
            continue

        category_name = row.get("category") or row.get("Категория") or ""
        category_key = normalize_category(category_name)
        sale_price = apply_markup(cost)
        sku = str(row.get("sku") or row.get("Артикул") or f"auto-{i}")

        new_catalog[category_key].append(
            Product(sku=sku, name=name, price=sale_price, category=CATEGORY_LABELS[category_key])
        )

    populated = {k: v for k, v in new_catalog.items() if v}
    if not populated:
        return False

    CATALOG.clear()
    CATALOG.update(populated)
    build_product_index()
    return True


def get_cart(user_data: Dict) -> Dict[str, int]:
    return user_data.setdefault("cart", {})


def get_admin_usernames() -> set[str]:
    raw = os.getenv("ADMIN_USERNAMES", "")
    admins = {
        name.strip().lstrip("@").lower()
        for name in raw.split(",")
        if name.strip()
    }
    return admins or DEFAULT_ADMIN_USERNAMES


def is_admin_username(username: str | None) -> bool:
    if not username:
        return False
    return username.lower() in get_admin_usernames()


def build_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛍 Каталог", callback_data="menu:catalog")],
            [InlineKeyboardButton("🧺 Корзина", callback_data="menu:cart")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="menu:help")],
        ]
    )


def build_categories_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(CATEGORY_LABELS.get(key, key), callback_data=f"cat:{key}")]
        for key in CATALOG.keys()
    ]
    rows.append([InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def build_products_menu(category_key: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                f"➕ {product.name} — {product.price}₽",
                callback_data=f"add:{product.sku}",
            )
        ]
        for product in CATALOG[category_key]
    ]
    rows.append([InlineKeyboardButton("⬅️ К категориям", callback_data="menu:catalog")])
    return InlineKeyboardMarkup(rows)


def build_cart_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Оформить заявку", callback_data="cart:checkout")],
            [InlineKeyboardButton("🗑 Очистить корзину", callback_data="cart:clear")],
            [InlineKeyboardButton("⬅️ В меню", callback_data="menu:main")],
        ]
    )


def render_cart(cart: Dict[str, int]) -> str:
    if not cart:
        return "Корзина пуста."

    lines = ["🧺 <b>Ваша корзина:</b>"]
    total = 0
    for sku, qty in cart.items():
        product = PRODUCTS_BY_SKU.get(sku)
        if not product:
            continue
        subtotal = product.price * qty
        total += subtotal
        lines.append(f"• {product.name} × {qty} = {subtotal}₽")

    lines.append(f"\nИтого: <b>{total}₽</b>")
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Мне есть 18 ✅", callback_data="age:yes")],
            [InlineKeyboardButton("Мне нет 18 ❌", callback_data="age:no")],
        ]
    )
    text = (
        "Привет! Этот бот предназначен только для совершеннолетних (18+).\n"
        "Подтвердите возраст, чтобы продолжить."
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard)


async def show_main_menu(query, text: str = "Главное меню:") -> None:
    await query.edit_message_text(text=text, reply_markup=build_main_menu())


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data or ""

    if data == "age:no":
        await query.edit_message_text(
            "Доступ ограничен. Возвращайтесь после достижения 18 лет."
        )
        return

    if data == "age:yes":
        context.user_data["age_verified"] = True
        await show_main_menu(query, "Возраст подтвержден ✅\n\nГлавное меню:")
        return

    if not context.user_data.get("age_verified"):
        await query.edit_message_text(
            "Сначала подтвердите возраст через /start."
        )
        return

    if data == "menu:main":
        await show_main_menu(query)
        return

    if data == "menu:catalog":
        await query.edit_message_text(
            "Выберите категорию:",
            reply_markup=build_categories_menu(),
        )
        return

    if data.startswith("cat:"):
        category_key = data.split(":", 1)[1]
        if category_key not in CATALOG:
            await query.edit_message_text("Категория не найдена.")
            return
        await query.edit_message_text(
            f"{CATEGORY_LABELS.get(category_key, category_key)} — выберите товар:",
            reply_markup=build_products_menu(category_key),
        )
        return

    if data.startswith("add:"):
        sku = data.split(":", 1)[1]
        product = PRODUCTS_BY_SKU.get(sku)
        if not product:
            await query.answer("Товар не найден", show_alert=True)
            return

        cart = get_cart(context.user_data)
        cart[sku] = cart.get(sku, 0) + 1
        await query.answer(f"Добавлено: {product.name}")
        return

    if data == "menu:cart":
        cart = get_cart(context.user_data)
        await query.edit_message_text(
            render_cart(cart), reply_markup=build_cart_menu(), parse_mode="HTML"
        )
        return

    if data == "cart:clear":
        context.user_data["cart"] = {}
        await query.edit_message_text(
            "Корзина очищена.", reply_markup=build_main_menu()
        )
        return

    if data == "cart:checkout":
        cart = get_cart(context.user_data)
        if not cart:
            await query.answer("Корзина пустая", show_alert=True)
            return

        admin_chat_id = os.getenv("ADMIN_CHAT_ID")
        user = query.from_user
        order_text = ["🧾 <b>Новая заявка</b>"]
        order_text.append(f"Покупатель: @{user.username or '-'} (id: {user.id})")
        order_text.append(render_cart(cart))
        order_text.append("\nСвяжитесь с клиентом для подтверждения заказа.")

        if admin_chat_id:
            try:
                await context.bot.send_message(
                    chat_id=admin_chat_id,
                    text="\n".join(order_text),
                    parse_mode="HTML",
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Не удалось отправить заявку админу: %s", exc)
                await query.answer(
                    "Ошибка отправки администратору", show_alert=True
                )
                return

        context.user_data["cart"] = {}
        await query.edit_message_text(
            "Заявка отправлена ✅\nСкоро с вами свяжется менеджер.",
            reply_markup=build_main_menu(),
        )
        return

    if data == "menu:help":
        await query.edit_message_text(
            "Как пользоваться:\n"
            "1) Откройте каталог\n"
            "2) Добавьте товары в корзину\n"
            "3) Нажмите 'Оформить заявку'\n\n"
            "Для проверки прав администратора: /admin\n\n"
            "Важно: продажи допускаются только в рамках законов вашей страны и для 18+.",
            reply_markup=build_main_menu(),
        )
        return


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        admin_note = "\n/admin — админ-проверка" if is_admin_username(update.effective_user.username if update.effective_user else None) else ""
        await update.message.reply_text(
            "Команды:\n/start — запуск и подтверждение возраста\n/help — помощь\n/whoami — показать ваш id/username\n/app — открыть mini app"
            f"{admin_note}"
        )


async def whoami_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    user = update.effective_user
    username = user.username if user else None
    user_id = user.id if user else None
    admin_status = "да" if is_admin_username(username) else "нет"

    await update.message.reply_text(
        "Ваши данные:\n"
        f"- id: {user_id}\n"
        f"- username: @{username or '-'}\n"
        f"- админ: {admin_status}"
    )


async def app_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    mini_app_url = os.getenv("MINI_APP_URL", "").strip()
    if not mini_app_url:
        await update.message.reply_text(
            "MINI_APP_URL не задан. Укажите HTTPS ссылку на mini app в .env"
        )
        return

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🚀 Открыть Mini App", web_app=WebAppInfo(url=mini_app_url))]]
    )
    await update.message.reply_text(
        "Откройте мини‑приложение кнопкой ниже:",
        reply_markup=keyboard,
    )


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    username = update.effective_user.username if update.effective_user else None
    if is_admin_username(username):
        await update.message.reply_text(
            f"✅ Вы администратор: @{username}"
        )
        return

    await update.message.reply_text("⛔ У вас нет прав администратора.")


def main() -> None:
    load_dotenv()
    build_product_index()

    try:
        loaded = load_catalog_from_price_source()
        if loaded:
            logger.info("Price source loaded successfully. Items: %s", len(PRODUCTS_BY_SKU))
        else:
            logger.info("Using built-in catalog (PRICE_SOURCE is empty or invalid)")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to load PRICE_SOURCE: %s", exc)
        logger.info("Falling back to built-in catalog")

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Не найден BOT_TOKEN в переменных окружения")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("whoami", whoami_cmd))
    app.add_handler(CommandHandler("app", app_cmd))
    app.add_handler(CallbackQueryHandler(on_button))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
