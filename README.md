# Telegram бот для сравнения цен на напитки/алкоголь в Lenta.com

Telegram бот для сравнения цен на напитки/алкоголь в Lenta.com по всем магазинам Москвы.

## Установка

```bash
pip install -r requirements.txt
playwright install chromium
```

## Настройка

Скопировать `.env.example` в `.env` и добавить токен бота:

```bash
cp .env.example .env
```

Отредактировать `.env` и указать токен:

```
BOT_TOKEN=your_telegram_bot_token_here
```

## Запуск

```bash
python main.py
```

## Использование

1. Отправить команду `/start`
2. Нажать кнопку "🔍 Искать в Ленте"
3. Ввести название товара
4. Выбрать товар из списка
5. Получить Excel файл с ценами по магазинам
