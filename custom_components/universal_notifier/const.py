# /config/custom_components/universal_notifier/const.py

DOMAIN = "universal_notifier"

# --- Chiavi di Configurazione (YAML) ---
CONF_CHANNELS = "channels"
CONF_ASSISTANT_NAME = "assistant_name"
CONF_DATE_FORMAT = "date_format"
CONF_GREETINGS = "greetings"
CONF_TIME_SLOTS = "time_slots"
CONF_DND = "dnd"

# --- Chiavi Parametri Servizio (Service Call) ---
# Usiamo queste costanti sia nello schema che nel codice
CONF_MESSAGE = "message"
CONF_TITLE = "title"
CONF_TARGETS = "targets"
CONF_DATA = "data"          # Dati extra generici
CONF_TARGET_DATA = "target_data"
CONF_PRIORITY = "priority"
CONF_SKIP_GREETING = "skip_greeting"
CONF_INCLUDE_TIME = "include_time"
CONF_OVERRIDE_GREETINGS = "override_greetings"
CONF_BOLD_PREFIX = "bold_prefix"

# --- Chiavi Canale Singolo ---
CONF_SERVICE = "service"
CONF_SERVICE_DATA = "service_data"
CONF_TARGET = "target"
CONF_ENTITY_ID = "entity_id"
CONF_IS_VOICE = "is_voice"
CONF_ALT_SERVICES = "alt_services"
CONF_TYPE = "type"

# --- Defaults ---
DEFAULT_NAME = "Hal9000"
DEFAULT_DATE_FORMAT = "%H:%M:%S"
DEFAULT_INCLUDE_TIME = True
DEFAULT_BOLD_PREFIX = True

# --- Default Time Slots & Volumes ---
# Definisce quando inizia la fascia e il volume (0.0 - 1.0) di default per quella fascia
DEFAULT_TIME_SLOTS = {
    "morning":   {"start": "07:00", "volume": 0.35},
    "afternoon": {"start": "12:00", "volume": 0.4},
    "evening":   {"start": "19:00", "volume": 0.3},
    "night":     {"start": "22:00", "volume": 0.1},
}

# --- Default DND (Do Not Disturb) ---
# Se non configurato, il DND è disabilitato di default (start == end)
DEFAULT_DND = {"start": "23:00", "end": "06:00"}

# --- Priority Settings ---
PRIORITY_VOLUME = 0.9  # Volume al 90% se priority=True

# --- Default Greetings ---
DEFAULT_GREETINGS = {
    "morning": ["Buongiorno", "Ben alzato", "Salve", "Buondì"],
    "afternoon": ["Buon pomeriggio", "Ciao", "Ben ritrovato"],
    "evening": ["Buonasera", "Buona serata", "Ben tornato a casa"],
    "night": ["Buonanotte", "Sogni d'oro", "È tardi"],
}

# --- Companion App Commands ---
COMPANION_COMMANDS = [
    "TTS",
    "request_location_update",
    "clear_badge",
    "ble_write",
    "close_notifications",
    "clear_notification", 
    "remove_channel",
    "stop_tts",
    "app_launch",
    "update_sensors",
]
######################################################
