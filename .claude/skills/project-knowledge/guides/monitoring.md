# Мониторинг

## Назначение
Настройки логирования, метрик и алертов для продакшена.

---

## Логирование

### Уровни логов

| Уровень | Когда использовать | Пример |
|---------|-------------------|--------|
| DEBUG | Детальная отладка (только dev) | Значения переменных, SQL запросы |
| INFO | Нормальные события | "Пользователь зарегистрирован", "Платеж обработан" |
| WARNING | Подозрительное, но не критичное | "Retry запроса к API", "Медленный ответ" |
| ERROR | Ошибка, но приложение работает | "Не удалось отправить email" |
| CRITICAL | Приложение не может работать | "БД недоступна", "Нет BOT_TOKEN" |

### Формат лога

```python
import logging

logger = logging.getLogger(__name__)

# Структурированный лог
logger.info(
    "Payment processed",
    extra={
        "user_id": user.id,
        "amount": payment.amount,
        "currency": "RUB"
    }
)
```

### Что логировать

**Обязательно:**
- Старт/стоп приложения
- Ошибки с traceback (`logger.exception()`)
- Важные бизнес-события (платежи, регистрации)
- Внешние API вызовы (запрос/ответ без sensitive данных)

**НЕ логировать:**
- Пароли и токены
- Персональные данные (телефоны, email полностью)
- Номера карт

---

## Отслеживание ошибок

**Инструмент:** [Sentry / Rollbar / логи / ...]

**Настройка Sentry (если используется):**
```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "development"),
    traces_sample_rate=0.1,
)
```

---

## Метрики

### Ключевые метрики

| Метрика | Описание | Порог алерта |
|---------|----------|--------------|
| Response time | Время ответа | > 5 секунд |
| Error rate | % ошибок | > 1% |
| Active users | DAU/MAU | Падение > 50% |

### Как собираем

```python
# Пример с prometheus (если используется)
from prometheus_client import Counter, Histogram

requests_total = Counter('requests_total', 'Total requests', ['endpoint'])
request_duration = Histogram('request_duration_seconds', 'Request duration')
```

---

## Health Checks

### Endpoint (если есть API)

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_db(),
        "redis": await check_redis(),
    }
```

### Что проверять

- [ ] База данных доступна
- [ ] Redis/кеш работает
- [ ] Внешние API отвечают
- [ ] Диск не заполнен
- [ ] Память в норме

---

## Alerting

### Каналы уведомлений

- **Критичные:** Telegram бот / SMS
- **Важные:** Email
- **Информационные:** Slack / Discord

### Триггеры алертов

| Событие | Приоритет | Куда |
|---------|-----------|------|
| Приложение упало | Critical | Telegram + SMS |
| БД недоступна | Critical | Telegram |
| Error rate > 5% | High | Telegram |
| Медленные ответы | Medium | Email |

---

## Ротация логов

```bash
# logrotate конфиг
/var/log/project/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 user user
}
```

---

## Дашборды (если есть)

**Grafana / Datadog / другое:**
- URL: [ссылка]
- Основные панели: [список]
