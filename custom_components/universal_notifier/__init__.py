# /config/custom_components/universal_notifier/__init__.py

"""Universal Notifier Component: wrapper avanzato per notifiche e assistenti vocali."""
import logging
import asyncio
import random
import html
import re
import unicodedata
import voluptuous as vol
import homeassistant.util.dt as dt_util
from datetime import time

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN, CONF_CHANNELS, CONF_ASSISTANT_NAME, CONF_DATE_FORMAT, 
    CONF_GREETINGS, CONF_IS_VOICE, CONF_OVERRIDE_GREETINGS, CONF_INCLUDE_TIME,
    CONF_TIME_SLOTS, CONF_DND, CONF_PRIORITY, CONF_VOLUME_ENTITY,
    CONF_SERVICE, CONF_SERVICE_DATA, CONF_TARGET, CONF_ENTITY_ID, 
    CONF_ALT_SERVICES, CONF_TYPE,
    DEFAULT_NAME, DEFAULT_DATE_FORMAT, DEFAULT_GREETINGS, DEFAULT_INCLUDE_TIME,
    DEFAULT_TIME_SLOTS, DEFAULT_DND, PRIORITY_VOLUME, COMPANION_COMMANDS
)

_LOGGER = logging.getLogger(__name__)

# --- HELPER FUNCTIONS PER SANITIZZAZIONE ---

def clean_text_for_tts(text: str) -> str:
    """Pulisce il testo per una migliore lettura TTS (no emoji, no html, no url)."""
    if not text: return ""
    # 1. Rimuovi HTML
    text = re.sub(r'<[^>]+>', '', text)
    # 2. Rimuovi URL (http/https)
    text = re.sub(r'http\S+', '', text)
    # 3. Rimuovi caratteri Markdown rumorosi (*, _, `, ~)
    text = re.sub(r'[*_`~]', '', text)
    # 4. Rimuovi Emojis e Simboli grafici (Categoria Unicode 'So' = Symbol, other)
    #    Mantiene lettere (L), numeri (N), punteggiatura (P), separatori (Z), simboli valuta (Sc)
    text = "".join(c for c in text if not unicodedata.category(c).startswith('So'))
    # 5. Normalizza spazi bianchi (rimuove doppi spazi, newline eccessivi)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def escape_markdown_v2(text: str) -> str:
    """Esegue l'escape dei caratteri riservati per MarkdownV2."""
    if not text: return ""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)

def sanitize_text_visual(text: str, parse_mode: str) -> str:
    """Pulisce il testo per la visualizzazione (Telegram/Notifiche)."""
    if not text: return ""
    mode = parse_mode.lower() if parse_mode else ""
    
    if "markdown" in mode:
        return escape_markdown_v2(text)
    elif "html" in mode:
        return html.escape(text, quote=False)
    
    return text

# --- SCHEMI DI VALIDAZIONE ---

TIME_SLOT_SCHEMA = vol.Schema({
    vol.Required("start"): cv.time,          
    vol.Optional("volume", default=0.5): vol.All(vol.Coerce(float), vol.Range(min=0, max=1))
})

TIME_SLOTS_CONFIG_SCHEMA = vol.Schema({
    vol.Optional("morning", default=DEFAULT_TIME_SLOTS["morning"]): TIME_SLOT_SCHEMA,
    vol.Optional("afternoon", default=DEFAULT_TIME_SLOTS["afternoon"]): TIME_SLOT_SCHEMA,
    vol.Optional("evening", default=DEFAULT_TIME_SLOTS["evening"]): TIME_SLOT_SCHEMA,
    vol.Optional("night", default=DEFAULT_TIME_SLOTS["night"]): TIME_SLOT_SCHEMA,
})

DND_SCHEMA = vol.Schema({
    vol.Optional("start", default=DEFAULT_DND["start"]): cv.time,
    vol.Optional("end", default=DEFAULT_DND["end"]): cv.time,
})

GREETINGS_SCHEMA = vol.Schema({
    vol.Optional("morning", default=DEFAULT_GREETINGS["morning"]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("afternoon", default=DEFAULT_GREETINGS["afternoon"]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("evening", default=DEFAULT_GREETINGS["evening"]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("night", default=DEFAULT_GREETINGS["night"]): vol.All(cv.ensure_list, [cv.string]),
})

ALT_SERVICE_ITEM_SCHEMA = vol.Schema({
    vol.Required(CONF_SERVICE): cv.string,
    vol.Optional(CONF_SERVICE_DATA): dict,
})

CHANNEL_SCHEMA = vol.Schema({
    vol.Required(CONF_SERVICE): cv.string,
    vol.Optional(CONF_IS_VOICE, default=False): cv.boolean,
    vol.Optional(CONF_ENTITY_ID): cv.entity_ids,
    vol.Optional(CONF_VOLUME_ENTITY): cv.entity_ids,
    vol.Optional(CONF_TARGET): vol.Any(cv.string, int, list),
    vol.Optional(CONF_SERVICE_DATA): dict,
    vol.Optional(CONF_ALT_SERVICES): vol.Schema({
        cv.string: ALT_SERVICE_ITEM_SCHEMA
    }),
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_ASSISTANT_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_DATE_FORMAT, default=DEFAULT_DATE_FORMAT): cv.string,
        vol.Optional(CONF_INCLUDE_TIME, default=DEFAULT_INCLUDE_TIME): cv.boolean,
        vol.Optional(CONF_GREETINGS, default=GREETINGS_SCHEMA({})): GREETINGS_SCHEMA,
        vol.Optional(CONF_TIME_SLOTS, default=TIME_SLOTS_CONFIG_SCHEMA({})): TIME_SLOTS_CONFIG_SCHEMA,
        vol.Optional(CONF_DND, default=DND_SCHEMA({})): DND_SCHEMA,
        vol.Required(CONF_CHANNELS): vol.Schema({
            cv.string: CHANNEL_SCHEMA
        }),
    }),
}, extra=vol.ALLOW_EXTRA)

# --- HELPER FUNCTIONS ---

def is_time_in_range(start: time, end: time, now: time) -> bool:
    if start <= end:
        return start <= now < end
    else:
        return start <= now or now < end

def get_current_slot_info(time_slots_conf, now_time):
    slots = []
    for key, data in time_slots_conf.items():
        slots.append((data["start"], key, data["volume"]))
    slots.sort(key=lambda x: x[0])
    found_key = None
    found_vol = None
    for start, key, vol in slots:
        if now_time >= start:
            found_key = key
            found_vol = vol
        else:
            break
    if found_key is None and slots:
        last_slot = slots[-1] 
        found_key = last_slot[1]
        found_vol = last_slot[2]
    return found_key, found_vol

# --- MAIN SETUP ---

async def async_setup(hass: HomeAssistant, config: dict):
    if DOMAIN not in config: return True
    
    conf = config[DOMAIN]
    channels_config = conf.get(CONF_CHANNELS, {})
    
    base_greetings = conf.get(CONF_GREETINGS) 
    time_slots_conf = conf.get(CONF_TIME_SLOTS)
    dnd_conf = conf.get(CONF_DND)
    global_name = conf.get(CONF_ASSISTANT_NAME)
    global_date_fmt = conf.get(CONF_DATE_FORMAT)
    global_include_time = conf.get(CONF_INCLUDE_TIME)

    async def async_send_notification(call: ServiceCall):
        # 1. Parsing Input
        global_raw_message = call.data.get("message", "")
        title = call.data.get("title")
        runtime_data = call.data.get("data", {})
        target_specific_data = call.data.get("target_data", {})
        targets = call.data.get("targets", [])
        
        override_name = call.data.get("assistant_name", global_name)
        skip_greeting = call.data.get("skip_greeting", False)
        include_time = call.data.get(CONF_INCLUDE_TIME, global_include_time)
        is_priority = call.data.get(CONF_PRIORITY, False)
        
        # 2. Contesto Temporale
        now = dt_util.now()
        now_time = now.time()
        
        slot_key, slot_volume = get_current_slot_info(time_slots_conf, now_time)
        is_dnd_active = is_time_in_range(dnd_conf["start"], dnd_conf["end"], now_time)
        
        # 3. Preparazione Saluti
        override_greetings_data = call.data.get(CONF_OVERRIDE_GREETINGS)
        effective_greetings = base_greetings 
        if override_greetings_data:
            effective_greetings = base_greetings.copy() 
            for key, value in override_greetings_data.items():
                if key in effective_greetings:
                    if not isinstance(value, list): value = [value]
                    effective_greetings[key] = value

        options = effective_greetings.get(slot_key, [])
        current_greeting = random.choice(options) if options and not skip_greeting else ""
        
        # Prefisso Visuale (non usato per TTS)
        prefix_parts = [f"[{override_name}"]
        if include_time:
            current_time_str = now.strftime(global_date_fmt)
            prefix_parts.append(f" - {current_time_str}")
        raw_prefix_text = "".join(prefix_parts) + "] "
        
        if isinstance(targets, str): targets = [targets]
        tasks = []

        # 4. Iterazione sui TARGETS
        for target_alias in targets:
            if target_alias not in channels_config:
                _LOGGER.warning(f"UniNotifier: Target '{target_alias}' sconosciuto.")
                continue

            channel_conf = channels_config[target_alias]
            
            # A. Override Messaggio
            specific_data = {}
            if target_alias in target_specific_data:
                specific_data = target_specific_data[target_alias].copy()
            
            target_raw_message = specific_data.pop("message", global_raw_message)

            # B. Determinazione Servizio
            service_type = specific_data.pop(CONF_TYPE, runtime_data.get(CONF_TYPE, None))
            alt_services_conf = channel_conf.get(CONF_ALT_SERVICES, {})
            
            if service_type and service_type in alt_services_conf:
                target_service_conf = alt_services_conf[service_type]
                full_service_name = target_service_conf[CONF_SERVICE]
                base_service_payload = target_service_conf.get(CONF_SERVICE_DATA, {})
                is_voice_channel = False 
            else:
                full_service_name = channel_conf[CONF_SERVICE]
                base_service_payload = channel_conf.get(CONF_SERVICE_DATA, {})
                is_voice_channel = channel_conf[CONF_IS_VOICE]

            # C. Check Comandi
            is_command_message = False
            if target_raw_message in COMPANION_COMMANDS or str(target_raw_message).startswith("command_"):
                is_command_message = True

            # D. Costruzione e Pulizia Messaggi
            
            # Parse Mode (Default: HTML per Telegram)
            parse_mode = specific_data.get("parse_mode", runtime_data.get("parse_mode"))
            if not parse_mode and "telegram_bot" in full_service_name:
                parse_mode = "html"

            if is_command_message:
                final_msg = target_raw_message
            else:
                if is_voice_channel:
                    # PULIZIA TTS: No emoji, no html, no doppi spazi
                    clean_msg = clean_text_for_tts(str(target_raw_message))
                    clean_greet = clean_text_for_tts(current_greeting)
                    final_msg = f"{clean_greet}. {clean_msg}" if clean_greet else clean_msg
                else:
                    # PULIZIA VISIVA: Escape caratteri speciali
                    clean_prefix = sanitize_text_visual(raw_prefix_text, parse_mode)
                    clean_msg = sanitize_text_visual(str(target_raw_message), parse_mode)
                    clean_greet = sanitize_text_visual(current_greeting, parse_mode)
                    
                    greeting_part = f"{clean_greet}. " if clean_greet else ""
                    final_msg = f"{clean_prefix}{greeting_part}{clean_msg}"
            
            # E. Determinazione Volume e Priority (Slot vs Override)
            override_volume = specific_data.get("volume", runtime_data.get("volume"))
            if override_volume is not None:
                try: target_volume = float(override_volume)
                except ValueError: target_volume = slot_volume
            elif is_priority:
                target_volume = PRIORITY_VOLUME
            else:
                target_volume = slot_volume

            # F. Gestione Broadcast (Lista Destinatari)
            configured_targets = channel_conf.get(CONF_TARGET)
            configured_entity_id = channel_conf.get(CONF_ENTITY_ID)
            
            destinations = []
            if configured_targets:
                if isinstance(configured_targets, list): destinations = configured_targets
                else: destinations = [configured_targets]
            elif configured_entity_id:
                # Fallback entity_id
                pass 

            if not destinations: destinations = [None] 

            # G. Loop Destinatari (Per evitare limiti API Telegram su liste)
            for dest in destinations:
                
                # Check DND e Volume (Solo Voce)
                if is_voice_channel:
                    if is_dnd_active and not is_priority and override_volume is None:
                        _LOGGER.info(f"UniNotifier: Skipped '{target_alias}' (DND attivo)")
                        continue
                    
                    volume_entity_id = channel_conf.get(CONF_VOLUME_ENTITY)
                    service_entity_id = channel_conf.get(CONF_ENTITY_ID)
                    effective_volume_entity = volume_entity_id if volume_entity_id else service_entity_id
                    
                    if effective_volume_entity:
                        tasks.append(hass.services.async_call(
                            "media_player", "volume_set", 
                            {"entity_id": effective_volume_entity, "volume_level": target_volume}
                        ))

                # Preparazione Payload
                try:
                    domain, service = full_service_name.split(".", 1)
                except ValueError: continue
                if domain not in hass.config.components: continue

                service_payload = base_service_payload.copy()
                
                if domain == "telegram_bot":
                    if "parse_mode" not in service_payload and parse_mode:
                        service_payload["parse_mode"] = parse_mode
                    if service_type in ["photo", "video"]: service_payload["caption"] = final_msg
                    else: service_payload["message"] = final_msg
                else:
                    service_payload["message"] = final_msg
                
                if title: service_payload["title"] = title
                
                # Assegnazione Target
                if dest:
                    if domain == "telegram_bot" or domain == "notify":
                        service_payload[CONF_TARGET] = dest
                    else:
                        service_payload[CONF_ENTITY_ID] = dest
                elif configured_entity_id:
                    service_payload[CONF_ENTITY_ID] = configured_entity_id

                # Merge Dati Accessori
                all_additional_data = {}
                if runtime_data: all_additional_data.update(runtime_data)
                if specific_data: all_additional_data.update(specific_data)
                
                for k in ["volume", CONF_TYPE, "parse_mode"]: all_additional_data.pop(k, None)

                if all_additional_data:
                    if domain == "notify":
                        if "data" not in service_payload: service_payload["data"] = {}
                        service_payload["data"].update(all_additional_data)
                    else:
                        service_payload.update(all_additional_data)

                tasks.append(hass.services.async_call(domain, service, service_payload))

        if tasks:
            await asyncio.gather(*tasks)

    hass.services.async_register(DOMAIN, "send", async_send_notification)
    return True
