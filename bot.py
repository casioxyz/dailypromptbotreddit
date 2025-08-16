import os
import sys
import datetime as dt
from zoneinfo import ZoneInfo

import praw
from openai import OpenAI

# ---- Secrets / Env ----
CLIENT_ID = os.environ["REDDIT_CLIENT_ID"]
CLIENT_SECRET = os.environ["REDDIT_CLIENT_SECRET"]
USERNAME = os.environ["REDDIT_USERNAME"]
PASSWORD = os.environ["REDDIT_PASSWORD"]
SUBREDDIT = os.environ["SUBREDDIT"]             # nur der Name, ohne /r/
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

TITLE_PREFIX = os.environ.get("TITLE_PREFIX", "🎨 Täglicher KI-Zeichenprompt")

# Uhrzeit-Check (nur wenn du willst, sonst einfach löschen)
POST_HOUR_BERLIN = os.environ.get("POST_HOUR_BERLIN")

berlin = ZoneInfo("Europe/Berlin")
now_berlin = dt.datetime.now(berlin)

if POST_HOUR_BERLIN is not None:
    try:
        post_hour = int(POST_HOUR_BERLIN)
        if now_berlin.hour != post_hour:
            print(f"[INFO] Nicht Post-Zeit ({now_berlin:%H:%M}). Beende.")
            sys.exit(0)
    except ValueError:
        print("[WARN] POST_HOUR_BERLIN ist nicht numerisch. Ignoriere Uhrzeit-Check.")

date_str = now_berlin.strftime("%d.%m.%Y")
title = f"{TITLE_PREFIX} – {date_str}"

# ---- Reddit ----
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=f"Daily AI Prompt Bot by u/{USERNAME}",
    username=USERNAME,
    password=PASSWORD,
)
subreddit = reddit.subreddit(SUBREDDIT)

# Doppelpost-Schutz
for s in subreddit.search(f'title:"{title}"', sort="new", time_filter="day"):
    if s.title.strip() == title.strip():
        print("[INFO] Heutiger Prompt existiert bereits. Beende.")
        sys.exit(0)

# ---- OpenAI ----
client = OpenAI(api_key=OPENAI_API_KEY)

system_message = (
    "Du bist ein kreativer Zeichenlehrer. "
    "Erzeuge GENAU EINEN Zeichnen-Prompt auf Englisch, 1–2 Sätze. "
    "Enthalten: Charakter(e), Twist/Idee, Stil/Technik oder Einschränkung, interessante Pose oder Perspektive. "
    "Verwende beliebige Zeichenstile, aber nur eigene Charaktere, keine bekannten Original-Charaktere wie Goku oder Naruto. Das Ziel ist es das Menschen ihre Kreativität fördern können und ihre zeichenkönste verbessern können. "
    "Keine Listen, keine Erklärungen, nur der Prompt-Text."
)

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    temperature=0.9,
    max_tokens=150,
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": "Bitte jetzt den heutigen Prompt."},
    ],
)

prompt_text = resp.choices[0].message.content.strip()

body = (
    f"Today's Prompt:\n\n**{prompt_text}**\n\n"
    f"Post your drawing in the comments. Have fun! ✍️"
)

# ---- Posten ----
submission = subreddit.submit(title=title, selftext=body)
print(f"✅ Gepostet: https://reddit.com{submission.permalink}")
