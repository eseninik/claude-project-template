# WORK ITEMS WORKFLOW

## Полный процесс

```
Context → User Spec → Tech Spec → Tasks → Code → UAT → Verification → Commit
```

## Для новой фичи

```
1. work/<feature-name>/
2. /new-user-spec → user-spec.md
3. /new-tech-spec → tech-spec.md + tasks/
4. Реализовать с skills
5. После деплоя → work/completed/
```

## Детали каждого этапа

### 1. Context Capture
- Понять требования пользователя
- Уточнить неясности
- Skill: `context-capture`

### 2. User Spec
- Описать фичу с точки зрения пользователя
- Acceptance criteria
- Command: `/new-user-spec`

### 3. Tech Spec
- Архитектурные решения
- Разбивка на задачи
- Command: `/new-tech-spec`

### 4. Implementation
- Выполнение tasks с skills
- Skill: `subagent-driven-development` или `executing-plans`

### 5. UAT
- Пользователь тестирует реальное поведение
- Skill: `user-acceptance-testing`

### 6. Verification
- Технические проверки
- Skill: `verification-before-completion`

### 7. Completion
- Коммит, пуш, опционально PR
- Skill: `finishing-a-development-branch`

---

## Когда использовать

**Загрузи этот файл при:**
- Начале новой фичи (нужна big picture)
- Вопросах "что дальше?" в процессе
- Объяснении процесса пользователю
