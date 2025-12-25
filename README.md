# 📢 Universal Notifier

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

Un componente custom per Home Assistant progettato per unificare l'invio di notifiche su piattaforme multiple (Telegram, Alexa, Google TTS, Mobile App, etc.). Include una logica intelligente per personalizzare i messaggi con l'ora, un nome assistente (es. Hal9000) e saluti casuali (es. Buongiorno/Buonasera) che variano in base all'orario.

Il componente verifica automaticamente quali integrazioni sono caricate su Home Assistant e instrada il messaggio solo verso i servizi disponibili.

## ✨ Caratteristiche Principali

* **Piattaforma Agnostica:** Invia notifiche a servizi di messaggistica (`notify.*`), bot (`telegram_bot.*`), e servizi TTS (`tts.*`) tramite un'unica chiamata.
* **Intelligenza Vocale vs Testuale:** Distingue automaticamente tra canali testuali (Telegram, Mail) e vocali (Alexa, Google TTS) per formattare il messaggio in modo appropriato.
    * **Testo:** Aggiunge il prefisso `[Nome Assistente - HH:MM:SS] Saluto.`
    * **Voce:** Invia solo il testo naturale `Saluto. Messaggio.`
* **Personalità Configurabile:** Nome assistente, formato orario e liste di saluti random sono configurabili in `configuration.yaml` e sovrascrivibili ad ogni chiamata.
* **Controllo dell'Orario:** Possibilità di disattivare l'inclusione dell'orario nel prefisso in modo globale o per singola chiamata.

## 🚀 Installazione (tramite HACS)

1.  Assicurati di avere [HACS](https://hacs.xyz/) installato e configurato in Home Assistant.
2.  In Home Assistant, vai su **HACS** -> **Integrazioni**.
3.  Clicca sui tre puntini in alto a destra e seleziona **"Custom repositories"**.
4.  Inserisci l'URL del repository: `https://github.com/jumping2000/universal_notifier`.
5.  Scegli la categoria **"Integration"** e clicca su **"Add"**.
6.  Cerca "Universal Notifier" nella sezione Integrazioni di HACS e installalo.
7.  **Riavvia Home Assistant.**

## ⚙️ Configurazione (Configuration.yaml)

Aggiungi il blocco `universal_notifier` nel tuo file `configuration.yaml`.

```yaml
# configuration.yaml

universal_notifier:
  # --- Configurazione Generale ---
  assistant_name: "HAL 9000"         # Nome dell'assistente nel prefisso [Nome - Ora]
  date_format: "%H:%M:%S"            # Formato dell'orario (es. 15:30:25)
  include_time: true                 # Se impostato su false, omette l'orario dal prefisso [Nome]
  
  # --- Saluti Personalizzati (Opzionale) ---
  # Se non specificati, verranno usati i default di sistema. 
  # Accetta una singola stringa o una lista di stringhe (una verrà scelta a caso).
  greetings:
    morning:
      - "Buongiorno Dave"       # 05:00 - 11:59
      - "Buona giornata"
    afternoon: 
      - "Buon pomeriggio"       # 12:00 - 17:59
    evening: 
      - "Buonasera a tutti"      # 18:00 - 21:59
    night: 
      - "Buonanotte."           # 22:00 - 04:59

  # --- Canali di Notifica (Alias) ---
  channels:
    # 1. Canale Telegram (Testo)
    telegram_admin:
      service: telegram_bot.send_message
      target: 123456789             # Il tuo Chat ID
      is_voice: false               # Default, ma esplicitato per chiarezza

    # 2. Canale Google Home (VOCE)
    google_cucina:
      service: tts.google_translate_say
      entity_id: media_player.google_home_cucina
      is_voice: true                # **Cruciale**: rimuove il prefisso [Nome - Ora]

    # 3. Canale Alexa (VOCE, tramite alexa_media_player)
    alexa_salotto:
      service: notify.alexa_media_echo_dot_salotto
      service_data:
        type: tts
      is_voice: true

    # 4. Canale Mobile App (Testo)
    my_phone:
      service: notify.mobile_app_iphone_di_mario
