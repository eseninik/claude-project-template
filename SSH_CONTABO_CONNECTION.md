# SSH Connection - Contabo Production Server

> **Копируй этот файл в любой проект для быстрого доступа к серверу**

---

## Server Info

- **Host:** 173.212.204.36 (Contabo Cloud VPS 30 NVMe)
- **User:** root (или admin — оба работают)
- **Auth:** SSH key (~/.ssh/id_ed25519) — **пароль отключён** (SSH hardening применён 2026-03-02)
- **OS:** Ubuntu 24.04.4 LTS (Noble Numbat)
- **Resources:** 23GB RAM, 193GB NVMe SSD
- **IPv6:** 2a02:c207:2310:7658::1/64

---

## Quick Connect

```bash
ssh -o StrictHostKeyChecking=no root@173.212.204.36
```

---

## For Claude Agent

**Используй эту команду для подключения к серверу:**

```bash
ssh -o StrictHostKeyChecking=no root@173.212.204.36 "<COMMAND>"
```

**Примеры:**

```bash
# Проверить статус сервиса
ssh -o StrictHostKeyChecking=no root@173.212.204.36 "systemctl status <service-name> --no-pager"

# Посмотреть логи
ssh -o StrictHostKeyChecking=no root@173.212.204.36 "journalctl -u <service-name> -n 50"

# Перезапустить сервис
ssh -o StrictHostKeyChecking=no root@173.212.204.36 "systemctl restart <service-name>"

# Git статус
ssh -o StrictHostKeyChecking=no root@173.212.204.36 "cd /root/<project-name> && git status"

# Выполнить команду в проекте
ssh -o StrictHostKeyChecking=no root@173.212.204.36 "cd /root/<project-name> && <command>"
```

---

## Common Project Paths

- Call Rate Bot: `/root/Call-rate-bot`
- Conference Bot: `/root/conference-bot`
- D-Brain: `/root/agent-second-brain`
- DocCheck Bot: `/root/doccheck-bot`
- Knowledge Bot: `/root/Knowledge-bot`
- Legal Bot: `/root/legal-bot`
- Quality Control Bot: `/root/quality-control-bot`
- Client Bot: `/root/client-bot`

---

## Bash Alias (Optional)

Добавь в `~/.bashrc` или `~/.bash_profile`:

```bash
alias contabo='ssh -o StrictHostKeyChecking=no root@173.212.204.36'
```

Потом можно использовать:
```bash
contabo
contabo "systemctl status my-service"
contabo "cd /root/my-project && git pull"
```
