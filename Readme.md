# ToDo Bot Project

Телеграм-бот для управления задачами с бекендом на Django и уведомлениями через Celery.

### Компоненты системы:

- **Backend**: Django 5 + DRF + SimpleJWT
- **Bot (Aiogram)**: Телеграм-бот с диалоговым интерфейсом
- **PostgreSQL**: Основная база данных
- **Redis**: Брокер сообщений для Celery
- **Celery Worker**: Фоновая обработка уведомлений
- **Celery Beat**: Планировщик периодических задач

### Технологический стек:

- **Backend**: Django 5.2, Django REST Framework, Simple JWT
- **Bot**: Aiogram 3.x, Aiogram Dialog
- **Database**: PostgreSQL 13
- **Queue**: Redis, Celery
- **Containerization**: Docker, Docker Compose

### Предварительные требования:

- Docker
- Docker Compose
- Telegram Bot Token от [@BotFather](https://t.me/BotFather)

## 🔧 API Endpoints

**Основные endpoints:**

```
GET/POST /api/tasks/ - Работа с задачами
GET/PATCH/DELETE /api/tasks/{id}/ - Детали задачи
POST /api/tasks/{id}/toggle_complete/ - Переключение статуса
GET/POST /api/categories/ - Работа с категориями
POST /api/bot/token/ - Аутентификация бота
POST /api/bot/register-user/ - Регистрация пользователя
```

## 🚀 Быстрый запуск

### Шаги для запуска:

1. **Клонируйте репозиторий:**

```bash
  git clone <repository-url>
  cd django_work
```

2. Создайте файл `.env` в директории `django_work/` со следующими параметрами по аналогии example.env:

```env
# Database
POSTGRES_DB=todo_db
POSTGRES_USER=todo_user
POSTGRES_PASSWORD=todo_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql://todo_user:todo_password@postgres:5432/todo_db

# Redis
REDIS_URL=redis://redis:6379/0

# Telegram Bot
BOT_TOKEN=your_token

# API URLs
API_BASE_URL=http://backend:8000/api
BOT_API_URL=http://bot:8001/send_message

# Timezone
TIME_ZONE=America/Adak
```

3. Запустите приложение с помощью Docker Compose:

```bash
# Сборка и запуск всех сервисов
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up -d --build

# Остановка всех сервисов
docker-compose down
```

## ⚙️ Особенности реализации

### Генерация ID:

```python
def generate_id(prefix: str, *args) -> str:
    date_part = datetime.date.today().strftime("%Y%m%d")
    base = "_".join(map(str, args))
    hash_part = hashlib.sha1(base.encode()).hexdigest()[:6]
    return f"{prefix}_{date_part}_{hash_part}"
```

### Уведомления через Celery:

- Проверка просроченных задач
- Автоматическая отправка уведомлений в Telegram
- Отметка отправленных уведомлений

### Диалоговый интерфейс:

- Пошаговое создание задач
- Выбор категорий через Multiselect
- Подтверждение перед сохранением

### Структура проекта

```
django_work/
├── backend/                 # Django приложение
│   ├── tasks/              # Основное приложение
│   │   ├── models.py       # Модели Task, Category, BotProfile
│   │   ├── views.py        # API ViewSets
│   │   ├── serializers.py  # DRF сериализаторы
│   │   ├── tasks.py        # Celery задачи
│   ├── todo_project/       # Настройки Django
│   └── manage.py
├── bot/                    # Telegram бот
│   ├── config/             # Конфигурация
│   ├── core/               # Ядро приложения
│   ├── dialogs/            # Диалоги Aiogram Dialog
│   ├── models/             # Pydantic схемы
│   ├── services/           # Клиенты API
│   └── main.py             # Точка входа
├── docker-compose.yml
├── .env.example
└── README.md
```