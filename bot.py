import asyncio
import logging
import re
from pathlib import Path

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())


# ===================== FSM СОСТОЯНИЯ =====================

class AdRequestState(StatesGroup):
    waiting_for_message = State()


# ===================== КЛАВИАТУРЫ =====================

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота @tokazakhstan_bot («Пограничник»)"""
    keyboard = [
        [InlineKeyboardButton(text="🗓 Запись на консультацию", callback_data="menu_consultation")],
        [InlineKeyboardButton(text="📖 Гайд по переезду в Казахстан", callback_data="menu_guide")],
        [InlineKeyboardButton(text="⭐ Отзывы", url=config.REVIEWS_URL)],
        [
            InlineKeyboardButton(text="👩‍💼 Обо мне", url=config.ABOUT_URL),
            InlineKeyboardButton(text="🏛 О юридической компании", url=config.COMPANY_URL),
        ],
        [InlineKeyboardButton(text="📢 Запрос по рекламе", callback_data="menu_ad_info")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_consultation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура раздела Консультации"""
    keyboard = [
        [InlineKeyboardButton(text="💬 Написать юристу", url=config.LAWYER_CONTACT_URL)],
        [InlineKeyboardButton(text="ℹ️ Подробнее о комплексной консультации", url=config.CONSULTATION_MORE_URL)],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_guide_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура раздела Гайд по переезду"""
    keyboard = [
        [InlineKeyboardButton(text="ℹ️ Подробнее о гайде", url=config.GUIDE_MORE_URL)],
        [InlineKeyboardButton(text="💳 КУПИТЬ ГАЙД", url=config.GUIDE_BUY_URL)],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ad_info_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура экрана условий рекламы"""
    keyboard = [
        [InlineKeyboardButton(text="✍️ Направить запрос на рекламу", callback_data="start_ad_input")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cancel_ad_keyboard() -> InlineKeyboardMarkup:
    """Кнопка отмены при вводе рекламного поста"""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_main")]]
    )


# ===================== ТЕКСТЫ =====================

WELCOME_TEXT = (
    "<b>Здравствуйте! Рада приветствовать вас!</b> 🇰🇿\n\n"
    "Я — <b>Олеся Аблёзгова</b>, кандидат юридических наук, учредитель Правового агентства <b>«РЕАКЦИЯ»</b> "
    "и автор экспертного канала о релокации <b>«Едем в Казахстан»</b>.\n\n"
    "С помощью бота «Пограничник» вы сможете:\n"
    "• <b>Записаться на юридическую консультацию</b>;\n"
    "• <b>Приобрести Гайд по переезду в Казахстан</b>;\n"
    "• <b>Обратиться по поводу размещения рекламы</b> в канале «Едем в Казахстан».\n\n"
    "Выберите нужный раздел в меню ниже 👇"
)

CONSULTATION_TEXT = (
    "<b>⚖️ Юридическая консультация Олеси Аблёзговой</b>\n\n"
    "Консультации проводит кандидат юридических наук, специалист по релокации и международному частному праву.\n\n"
    "<b>Стоимость юридической консультации:</b>\n\n"
    "✅ <b>для физических лиц по гражданским делам по российскому праву</b> — от 5 000 рублей;\n\n"
    "✅ <b>для физических лиц по налоговым, банковским вопросам; воинскому учёту; легализации в РК (оформление РВП, ВНЖ)</b> — от 7 000 рублей;\n\n"
    "✅ <b>комплексная консультация по релокации</b> (стратегия переезда, налоги, имущество, открытие бизнеса, легализация) — от 10 000 рублей;\n\n"
    "✅ <b>консультации по коммерческим вопросам, иностранному праву, для юридических лиц</b> — от 15 000 рублей.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "<b>Порядок оказания услуги:</b>\n"
    "✅ согласование времени;\n"
    "✅ оплата консультации;\n"
    "✅ консультация в режиме телефонного разговора или видеосвязи (по вашему выбору).\n\n"
    "<b>Также возможна экспресс-консультация:</b>\n"
    "✅ вопросы голосовым сообщением (до 10 минут) или текстом;\n"
    "✅ оплата услуги;\n"
    "✅ ответ голосовым сообщением (до 15 минут) в течение 1–3 часов в рабочие дни.\n"
    "<i>Стоимость экспресс-консультации: 3 000 рублей.</i>\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Просьба уточнить ваш вопрос перед выбором. Для некоторых ситуаций возможна только индивидуальная консультация (налоговые вопросы, семейные споры и др).\n\n"
    "Перед консультацией по релокации, а также по налоговым и банковским вопросам, необходим примерный список ваших вопросов и краткое описание ситуации.\n\n"
    "В ходе консультации вы получите правовую оценку ситуации и информацию о необходимых дальнейших действиях.\n\n"
    "Для записи на консультацию или уточнения стоимости направьте краткое описание вашей ситуации 👇"
)

GUIDE_TEXT = (
    "<b>📖 ГАЙД ПО ПЕРЕЕЗДУ В КАЗАХСТАН:</b>\n\n"
    "✅ <b>пошаговый ЮРИДИЧЕСКИЙ путеводитель</b>;\n"
    "✅ <b>30+ страниц</b> исключительно важной, актуальной и необходимой информации, которая позволит вам спокойно переехать в Казахстан;\n"
    "✅ <b>четкий план</b>: с чего начинать дома, куда бежать и что делать по приезду;\n"
    "✅ <b>разобраны все необходимые для обустройства нюансы</b>: документы, апостили, доверенности, деньги, животные, авто, выезд, ИИН, ЦОНы, ЭЦП, SIM-карты, телефоны, банки, жилье, работа, регистрация, РВП, ВНЖ.\n\n"
    "⚠️ <b>Ограничения использования:</b> гайд создан для граждан России по законодательству России и Казахстана.\n"
    "<i>Релокацию из других стран обсуждаем в рамках индивидуальной консультации.</i>\n\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "<b>Как это работает:</b>\n"
    "✅ оплата любой картой (через официальное приложение Telegram);\n"
    "✅ получение доступа к pdf-файлу;\n"
    "✅ внимательное изучение;\n"
    "✔️ переезд в Казахстан."
)

AD_INFO_TEXT = (
    "<b>📢 Размещение рекламы в канале «Едем в Казахстан» и чате «Переезд в Казахстан»</b>\n\n"
    "Для определения возможности и стоимости размещения рекламного поста, "
    "предварительно просим направить информацию о вашей рекламе:\n\n"
    "• <b>Примерный текст поста</b> со ссылками на рекламируемые товары, услуги или канал;\n"
    "• <b>Желаемую площадку</b> (канал или чат) и примерные даты публикации.\n\n"
    "⚠️ <i>Обратите внимание: без текста поста и ссылок на продукт заявки не рассматриваются.</i>\n\n"
    "Нажмите кнопку ниже, чтобы направить материалы 👇"
)


# ===================== ОБРАБОТЧИКИ КОМАНД =====================

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Стартовое меню"""
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=get_main_menu_keyboard())


@dp.message(Command("id", "myid"))
async def cmd_get_id(message: Message):
    """Помогает узнать свой Telegram ID для настройки ADMIN_ID"""
    await message.answer(
        f"Ваш числовой Telegram ID: <code>{message.from_user.id}</code>\n\n"
        "Укажите его в настройках Railway в переменной <b>ADMIN_ID</b>, чтобы бот пересылал вам запросы по рекламе!"
    )


@dp.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    try:
        await callback.message.edit_text(WELCOME_TEXT, reply_markup=get_main_menu_keyboard())
    except Exception:
        await callback.message.answer(WELCOME_TEXT, reply_markup=get_main_menu_keyboard())
    await callback.answer()


# ===================== РАЗДЕЛ: КОНСУЛЬТАЦИИ =====================

@dp.callback_query(F.data == "menu_consultation")
async def show_consultation(callback: CallbackQuery):
    await callback.message.edit_text(CONSULTATION_TEXT, reply_markup=get_consultation_keyboard())
    await callback.answer()


# ===================== РАЗДЕЛ: ГАЙД ПО ПЕРЕЕЗДУ =====================

@dp.callback_query(F.data == "menu_guide")
async def show_guide(callback: CallbackQuery):
    await callback.message.edit_text(GUIDE_TEXT, reply_markup=get_guide_keyboard())
    await callback.answer()


# ===================== РАЗДЕЛ: РЕКЛАМА (УСЛОВИЯ И ВВОД) =====================

@dp.callback_query(F.data == "menu_ad_info")
async def show_ad_info(callback: CallbackQuery, state: FSMContext):
    """Экран с условиями и фильтром для рекламодателей"""
    await state.clear()
    await callback.message.edit_text(AD_INFO_TEXT, reply_markup=get_ad_info_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "start_ad_input")
async def start_ad_input(callback: CallbackQuery, state: FSMContext):
    """Переход в режим ожидания текста поста"""
    await state.set_state(AdRequestState.waiting_for_message)
    prompt_text = (
        "✍️ <b>Отправьте текст вашего рекламного поста</b>\n\n"
        "Пришлите в ответном сообщении текст поста со ссылками на рекламируемые товары или услуги. "
        "Вы также можете прикрепить баннер или изображение к сообщению 👇"
    )
    await callback.message.edit_text(prompt_text, reply_markup=get_cancel_ad_keyboard())
    await callback.answer()


@dp.message(AdRequestState.waiting_for_message)
async def process_user_ad_message(message: Message, state: FSMContext):
    """Пользователь прислал рекламный пост -> пересылаем Олесе"""
    await state.clear()

    user_info = f"@{message.from_user.username}" if message.from_user.username else "без username"
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    content_text = message.text or message.caption or "<i>[Только медиафайл без текста]</i>"

    # Ответ клиенту
    await message.answer(
        "✅ <b>Спасибо! Ваш рекламный пост передан Олесе на согласование.</b>\n\n"
        "Она оценит возможность размещения и ответит вам прямо здесь, в этом чате бота.",
        reply_markup=get_main_menu_keyboard()
    )

    # Уведомление Олесе (ADMIN_ID)
    if config.ADMIN_ID:
        admin_header = (
            "📢 <b>НОВЫЙ ЗАПРОС ПО РЕКЛАМЕ!</b>\n\n"
            f"👤 <b>От:</b> {user_name} ({user_info})\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
            f"<b>Предложенный пост:</b>\n{content_text}\n\n"
            "────────────────────────\n"
            "💡 <i>Чтобы ответить рекламодателю прямо через бота, просто нажмите «Ответить / Reply» на это сообщение!</i>\n"
            f"#user_{user_id}"
        )
        try:
            if message.photo:
                await bot.send_photo(
                    chat_id=config.ADMIN_ID,
                    photo=message.photo[-1].file_id,
                    caption=admin_header
                )
            else:
                await bot.send_message(chat_id=config.ADMIN_ID, text=admin_header)
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу: {e}")
    else:
        logger.warning("ADMIN_ID не настроен! Запрос по рекламе не может быть доставлен.")


# ===================== ОТВЕТ ОЛЕСИ ЧЕРЕЗ РЕПЛАЙ =====================

@dp.message(F.chat.id == config.ADMIN_ID, F.reply_to_message)
async def process_admin_reply(message: Message):
    """Олеся отвечает на сообщение бота реплаем -> пересылаем ответ клиенту"""
    reply_text = message.reply_to_message.text or message.reply_to_message.caption or ""
    match = re.search(r"#user_(\d+)", reply_text)

    if not match:
        return  # Не наше служебное сообщение

    target_user_id = int(match.group(1))

    try:
        user_reply_text = (
            "💬 <b>Ответ по рекламе от Олеси:</b>\n\n"
            f"{message.text or ''}\n\n"
            "────────────────────────\n"
            "<i>(Вы можете написать ответное сообщение прямо сюда)</i>"
        )
        if message.photo:
            await bot.send_photo(
                chat_id=target_user_id,
                photo=message.photo[-1].file_id,
                caption=user_reply_text
            )
        else:
            await bot.send_message(chat_id=target_user_id, text=user_reply_text)

        await message.reply("✅ <b>Ответ успешно доставлен рекламодателю в бот!</b>")
    except Exception as e:
        logger.error(f"Ошибка при доставке ответа пользователю {target_user_id}: {e}")
        await message.reply(f"❌ Не удалось доставить сообщение (возможно, пользователь заблокировал бота). Ошибка: {e}")


# ===================== ЗАПУСК =====================

async def main():
    logger.info("Запуск бота «Пограничник» (@tokazakhstan_bot)...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
