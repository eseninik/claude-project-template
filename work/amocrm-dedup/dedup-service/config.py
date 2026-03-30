"""Configuration for amoCRM dedup service."""

import os
from dotenv import load_dotenv

load_dotenv()

# amoCRM
AMOCRM_DOMAIN = os.getenv("AMOCRM_DOMAIN", "migratoramocrm.amocrm.ru")
AMOCRM_BASE_URL = f"https://{AMOCRM_DOMAIN}/api/v4"
AMOCRM_CLIENT_ID = os.getenv("AMOCRM_CLIENT_ID")
AMOCRM_CLIENT_SECRET = os.getenv("AMOCRM_CLIENT_SECRET")
AMOCRM_REDIRECT_URI = os.getenv("AMOCRM_REDIRECT_URI", "https://example.com")

# Token file — persists across restarts
TOKEN_FILE = os.getenv("TOKEN_FILE", "tokens.json")

# Field IDs
LEAD_NICK_FIELD_ID = 1612133           # NICK field on leads (@username)
CONTACT_LOGIN_FIELD_ID = 1655001       # Логин field on contacts (username)
CONTACT_UMNICO_SOCIAL_ID = 1654991     # Umnico socialId field
CONTACT_UMNICO_CUSTOMER_ID = 1654993   # Umnico customerId field

# Pipeline
MAIN_PIPELINE_ID = 7323650             # Воронка
CLOSED_STATUS_ID = 143                 # Closed & not implemented
LOSS_REASON_FIELD_ID = 1631379         # Причина отказа
LOSS_REASON_DOUBLE_ENUM = 4661359      # Double

# Service
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8585"))

# Index refresh interval (seconds)
INDEX_REFRESH_INTERVAL = int(os.getenv("INDEX_REFRESH_INTERVAL", "3600"))  # 1 hour

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Merge cooldown (seconds) — skip re-merge if same contact pair was merged recently
MERGE_COOLDOWN_SECONDS = int(os.getenv("MERGE_COOLDOWN_SECONDS", "600"))  # 10 minutes

# Umnico field IDs to clear on new contact after merge
UMNICO_FIELD_IDS = [CONTACT_LOGIN_FIELD_ID, CONTACT_UMNICO_SOCIAL_ID, CONTACT_UMNICO_CUSTOMER_ID]

# Wazzup (WZ) field IDs on contacts
CONTACT_TG_USERNAME_WZ = 1648299       # TelegramUsername_WZ — used by Wazzup for dedup
CONTACT_TG_ID_WZ = 1648301             # TelegramId_WZ
CONTACT_TG_GROUP_ID_WZ = 1647905       # TelegroupId_WZ
