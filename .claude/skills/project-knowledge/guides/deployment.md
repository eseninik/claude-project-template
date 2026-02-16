# Деплой

## Назначение
Информация о деплое, environments и инфраструктуре.

---

## Платформа

**Хостинг:** [VPS / AWS / Heroku / ...]
**Сервер:** [Ubuntu 22.04 / ...]
**IP:** [xxx.xxx.xxx.xxx]

---

## SSH доступ

```bash
# Подключение
ssh user@server-ip

# Путь к проекту
cd /home/user/project-name
```

**SSH ключ:** `~/.ssh/id_ed25519` (или путь к ключу)

---

## Environments

### Production
- **URL:** [если есть]
- **Ветка:** `main`
- **Автодеплой:** При push в main

### Staging (если есть)
- **URL:** [если есть]
- **Ветка:** `dev`
- **Автодеплой:** При push в dev

### Local
- **Запуск:** `py -3.12 -m src.main` или `docker-compose up`

---

## Переменные окружения

**Обязательные:**
```env
BOT_TOKEN=           # Telegram bot token
DATABASE_URL=        # Строка подключения к БД
```

**Опциональные:**
```env
DEBUG=false          # Режим отладки
LOG_LEVEL=INFO       # Уровень логирования
```

**Где хранятся:**
- Local: `.env` файл (НЕ в git!)
- Production: GitHub Secrets → GitHub Actions → сервер

---

## Триггеры деплоя

**Автоматический деплой:**
1. Push в `main` → GitHub Actions → SSH на сервер → git pull → restart

**Ручной деплой:**
```bash
ssh user@server
cd /home/user/project
git pull origin main
sudo systemctl restart project-name
```

---

## Systemd сервис

```ini
# /etc/systemd/system/project-name.service
[Unit]
Description=Project Name Bot
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/project
ExecStart=/usr/bin/python3 -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Команды:**
```bash
sudo systemctl status project-name   # Статус
sudo systemctl restart project-name  # Перезапуск
sudo journalctl -u project-name -f   # Логи
```

---

## Rollback процедуры

**Быстрый откат:**
```bash
ssh user@server
cd /home/user/project
git checkout HEAD~1  # Откат на предыдущий коммит
sudo systemctl restart project-name
```

**Полный откат к конкретной версии:**
```bash
git log --oneline    # Найти нужный коммит
git checkout <commit-hash>
sudo systemctl restart project-name
```

---

## Healthchecks

**Проверка работоспособности:**
- [ ] Бот отвечает на /start
- [ ] БД доступна
- [ ] Внешние API отвечают

**Мониторинг:** [UptimeRobot / Healthchecks.io / ...]
