# База данных

## Назначение
Информация о структуре БД, схемах и правилах работы с данными.

---

## Тип БД

**База данных:** [PostgreSQL / SQLite / MongoDB / Нет]
**ORM:** [SQLAlchemy / Tortoise / Raw SQL / N/A]
**Миграции:** [Alembic / вручную / N/A]

---

## Основные таблицы

<!-- Опиши ключевые таблицы/коллекции -->

### users
| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT PK | Telegram user ID |
| username | VARCHAR(255) | @username |
| created_at | TIMESTAMP | Дата регистрации |
| is_active | BOOLEAN | Активен ли пользователь |

### [другая_таблица]
| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL PK | Первичный ключ |
| ... | ... | ... |

---

## Связи между таблицами

```
users 1──M orders (user_id)
orders M──M products (order_items)
```

<!-- Или ERD диаграмма если сложная схема -->

---

## Constraints и индексы

**Уникальные:**
- `users.telegram_id` - один пользователь = один telegram ID

**Индексы:**
- `users.telegram_id` - поиск по telegram ID
- `orders.created_at` - сортировка заказов по дате

**Foreign Keys:**
- `orders.user_id` → `users.id` ON DELETE CASCADE

---

## Naming Conventions

- Таблицы: `snake_case`, множественное число (`users`, `orders`)
- Колонки: `snake_case` (`created_at`, `user_id`)
- Foreign keys: `<table>_id` (`user_id`, `order_id`)
- Индексы: `ix_<table>_<column>` (`ix_users_telegram_id`)

---

## Стратегия миграций

**Alembic workflow:**
```bash
# Создать миграцию
alembic revision --autogenerate -m "add users table"

# Применить миграции
alembic upgrade head

# Откатить последнюю
alembic downgrade -1
```

**Правила:**
- Каждое изменение схемы = отдельная миграция
- Всегда проверяй сгенерированный SQL перед применением
- Для production: сначала тестируй на staging

---

## Работа с sensitive данными

**Что шифруем:**
- Персональные данные (телефоны, email)
- Платежные данные

**Что маскируем в логах:**
- user_id вместо полных данных
- Последние 4 цифры телефона

**Что НЕ храним:**
- Пароли в открытом виде (только hash)
- Полные номера карт
