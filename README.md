# Telegram Twitter Bot

## Setup and Run

### Clone

```bash
git clone --branch master https://github.com/pourya90091/TelegramTwitterBot.git
```

### Install Requirements

```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

### Configuration
- Set settings at `/.env`.
    - **AUTH_TOKEN**: Will be used to log into a Twitter account, obtain it from your browser.
    Open your Browser, open https://twitter.com and login to an account, then open Developer Tools (F12) and open Application tab. Open Cookies from Storage section and copy the value of auth_token cookie, done, you now have your AUTH_TOKEN.
    - **BOT_TOKEN**: Will be used for Telegram bot, obtain it from https://t.me/BotFather.
    - **ADMINS**: Username(s) of who that can access to this bot. You should separate usernames with `, ` (comma and whitespace).
    - **TIMEOUT**: Don't touch it! (kidding, but really don't mess with it).

### Run

```bash
python bot.py
```

## Tips

>**Tip** : You should be aware that this program does not using Twitter API (directly).
---
