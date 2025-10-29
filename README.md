# Telegram Bot для поиска товаров в Ленте

Telegram бот на базе aiogram 3.x для поиска товаров на Lenta.com и сравнения цен по магазинам.

## Функционал

- 🔍 Поиск товаров в каталоге Lenta.com
- 📊 Сравнение цен по магазинам в Москве
- 📥 Экспорт результатов в Excel файл
- 🤖 Простой и интуитивный интерфейс

## Технологии

- **Python 3.11+**
- **aiogram 3.3.0** - асинхронный фреймворк для Telegram ботов
- **Playwright 1.40.0** - автоматизация браузера для парсинга
- **pandas 2.1.4** - обработка данных
- **openpyxl 3.1.2** - генерация Excel отчетов

## Быстрый старт

### Локальная разработка

#### 1. Создание виртуального окружения

```bash
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

#### 3. Установка браузера Playwright

```bash
playwright install chromium
# Linux (полная установка с системными зависимостями):
playwright install --with-deps chromium
```

#### 4. Настройка переменных окружения

Скопируйте пример конфигурации:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите токен бота:

```env
BOT_TOKEN=your_telegram_bot_token_here
LOG_LEVEL=INFO
PLAYWRIGHT_TIMEOUT=30000
LOCALE=ru-RU
```

#### 5. Запуск бота

```bash
python bot.py
```

### Развертывание с Docker (Рекомендуется)

#### 1. Настройка переменных окружения

```bash
cp .env.example .env
# Отредактируйте .env с вашим токеном
```

#### 2. Запуск с Docker Compose

```bash
docker-compose up -d
```

Просмотр логов:

```bash
docker-compose logs -f
```

Остановка:

```bash
docker-compose down
```

## Использование бота

1. **Запустите бота** - отправьте команду `/start`
2. **Нажмите кнопку** "🔍 Искать в Ленте"
3. **Введите название товара** (например, "водка")
4. **Выберите товар** из списка найденных
5. **Получите Excel файл** с ценами по магазинам

## Переменные окружения

| Переменная | Описание | По умолчанию | Обязательна |
|-----------|----------|--------------|-------------|
| `BOT_TOKEN` | Токен Telegram бота от [@BotFather](https://t.me/BotFather) | - | Да |
| `LOG_LEVEL` | Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO | Нет |
| `PLAYWRIGHT_TIMEOUT` | Таймаут загрузки страниц (мс) | 30000 | Нет |
| `LOCALE` | Локаль браузера (ru-RU, en-US, etc.) | ru-RU | Нет |

## Структура проекта

```
.
├── bot.py              # Основной файл Telegram бота
├── parser.py           # Парсинг Lenta.com с Playwright
├── excel_gen.py        # Генерация Excel отчетов
├── requirements.txt    # Python зависимости
├── Dockerfile          # Docker конфигурация
├── docker-compose.yml  # Docker Compose конфигурация
├── .env.example        # Пример переменных окружения
├── .gitignore         # Git игнорирование
└── README.md          # Документация
```

## Архитектура

### bot.py
Основной модуль бота с обработчиками:
- `/start` - приветствие с кнопкой поиска
- Обработчик кнопки "🔍 Искать в Ленте"
- Обработчик текстового ввода для поиска товаров
- Обработчик callback для выбора товара и получения цен

### parser.py
Функции для парсинга Lenta.com:
- `search_product(query)` - поиск товаров по запросу
- `get_prices_by_stores(product_id)` - получение цен по магазинам

### excel_gen.py
Генерация Excel отчетов:
- `create_excel(product_name, prices_data)` - создание Excel файла

## Решение проблем

### Playwright не запускается

```bash
# Переустановите браузеры
playwright install --with-deps chromium
```

### Таймауты при парсинге

Увеличьте таймаут в `.env`:
```env
PLAYWRIGHT_TIMEOUT=60000
```

### Ошибки shared memory в Docker

Добавьте в `docker-compose.yml`:
```yaml
services:
  bot:
    shm_size: '2gb'
```

### Проблемы с кодировкой

Убедитесь, что используете локаль `ru-RU`:
```env
LOCALE=ru-RU
```

## Разработка

### Тестирование парсера

```bash
python parser.py
```

### Тестирование генерации Excel

```bash
python excel_gen.py
```

### Отладка

Включите подробное логирование:
```env
LOG_LEVEL=DEBUG
```

## Безопасность

- ⚠️ Никогда не коммитьте файл `.env` в систему контроля версий
- 🔒 Храните токен бота в секрете
- 🐳 Docker контейнер работает от непривилегированного пользователя
- 🔐 Ограничивайте права бота при необходимости

## Лицензия

Проект предоставляется "как есть" в образовательных и разработческих целях.

## Поддержка

Документация:
- [aiogram](https://docs.aiogram.dev/)
- [Playwright Python](https://playwright.dev/python/)
- [Docker](https://docs.docker.com/)
