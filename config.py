import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота @tokazakhstan_bot (Пограничник)
BOT_TOKEN = os.getenv("BOT_TOKEN", "6386091051:AAEQDzPLG9xq_d59UiI1-umjhJ9CT7cBthA")

# Числовой Telegram ID Олеси (для получения запросов по рекламе и ответов через бота)
# Узнать свой ID можно в боте @userinfobot или отправив /id нашему боту
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Ссылки из главного меню
REVIEWS_URL = "https://t.me/tokazakhstan_2022/3317"
ABOUT_URL = "https://reaction64.ru/department"
COMPANY_URL = "https://reaction64.ru/relocation"

# Ссылки для раздела Консультации
LAWYER_CONTACT_URL = "https://t.me/lesja64"
CONSULTATION_MORE_URL = "https://reaction64.ru/relocation_kz"

# Ссылки для раздела Гайд по переезду
GUIDE_MORE_URL = "https://reaction64.ru/relocation_kz_guide"
GUIDE_BUY_URL = "https://web.tribute.tg/p/E1i"
