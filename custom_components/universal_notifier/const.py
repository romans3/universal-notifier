# /config/custom_components/universal_notifier/const.py

DOMAIN = "universal_notifier"
CONF_CHANNELS = "channels"

# Chiavi di configurazione (configuration.yaml)
CONF_ASSISTANT_NAME = "assistant_name"
CONF_DATE_FORMAT = "date_format"
CONF_GREETINGS = "greetings"
CONF_IS_VOICE = "is_voice"
CONF_INCLUDE_TIME = "include_time"

# Override Service Call Specifici
CONF_OVERRIDE_GREETINGS = "override_greetings"

# Default values
DEFAULT_NAME = "Jarvis"
DEFAULT_DATE_FORMAT = "%H:%M:%S"
DEFAULT_INCLUDE_TIME = True

# --- DEFAULT GREETINGS (LISTE RANDOM) ---
DEFAULT_GREETINGS = {
    "morning": [
        "Buongiorno",
        "Buona giornata",
        "Salve",
        "Buondì",
        "Hey, spero tu abbia dormito bene",
    ],
    "afternoon": [
        "Buon pomeriggio",
        "Ciao",
        "Ben ritrovato",
    ],
    "evening": [
        "Buonasera",
        "Buona serata",
        "Ben tornato a casa",
    ],
    "night": [
        "Buonanotte",
        "Sogni d'oro",
        "È tardi",
    ],
}
