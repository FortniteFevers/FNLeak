"""
monitors.py — Polling loops for auto-detecting Fortnite updates.

Fixes vs the original AutoLeak:
  - All recursive on-error calls replaced with proper while-loops
    (the original would stack-overflow after enough errors).
  - Centralised sleep + retry logic.
  - watch_cosmetics accepts an on_update callback so bot.py
    doesn't need to import image_gen directly here.
"""

from __future__ import annotations

import json
import io
import time
from typing import Callable

import requests
from colorama import Fore
from PIL import Image

FORTNITE_API    = "https://fortnite-api.com"
STAGING_URL     = "https://fortnite-public-service-stage.ol.epicgames.com/fortnite/api/version"
NOTICES_API     = "https://status.epicgames.com/api/v2/status.json"


def _cfg_delay(cfg: dict, default: int = 30) -> int:
    """Settings entries can arrive as CTkEntry strings."""
    try:
        return int(cfg.get("BotDelay", default))
    except (TypeError, ValueError):
        return default


def _get_json(url: str, params: dict | None = None, timeout: int = 15) -> dict | None:
    """GET + parse JSON, returning None on any error."""
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(Fore.RED + f"  Request failed ({url}): {e}")
        return None


# ── update mode ───────────────────────────────────────────────────────────────

def watch_cosmetics(
    cfg: dict,
    on_update: Callable[[], None],
    delay: int = 30,
    language: str = "en",
) -> None:
    """
    Poll fortnite-api.com for a change in the new-cosmetics hash.
    Calls on_update() whenever the hash changes.
    Runs until the user interrupts (Ctrl-C).
    """
    print(Fore.CYAN + f"\n-- Update Mode --  (delay={delay}s, lang={language})")
    print(Fore.YELLOW + "Press Ctrl-C to stop.\n")

    count      = 0
    old_hash   = None

    # Grab the initial hash
    while old_hash is None:
        data = _get_json(f"{FORTNITE_API}/v2/cosmetics/new", params={"language": language})
        if data:
            old_hash = data["data"]["hashes"]["br"]
        else:
            print(Fore.YELLOW + "  Waiting for API…")
            time.sleep(delay)

    try:
        while True:
            count += 1
            data = _get_json(f"{FORTNITE_API}/v2/cosmetics/new", params={"language": language})
            if data:
                new_hash = data["data"]["hashes"]["br"]
                print(Fore.GREEN + f"  Checking… ({count})", end="\r")
                if new_hash != old_hash:
                    print(Fore.CYAN + f"\n  [!] Hash changed — running update…")
                    on_update()
                    old_hash = new_hash
            time.sleep(delay)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nUpdate mode stopped.")


# ── BR news feed ──────────────────────────────────────────────────────────────

def watch_news(cfg: dict, tw) -> None:
    """Watch for changes in the Battle Royale news feed and tweet the new tile image."""
    from ALmodules.twitter_client import TwitterClient
    delay    = _cfg_delay(cfg)
    language = cfg["language"]
    name     = cfg["name"]

    print(Fore.CYAN + f"\n-- BR News Watcher --  (delay={delay}s)")
    print(Fore.YELLOW + "Press Ctrl-C to stop.\n")

    old_hash = None
    count    = 0

    try:
        while True:
            data = _get_json(f"{FORTNITE_API}/v2/news/br", params={"language": language})
            if data:
                news_hash = (data.get("data") or {}).get("hash")
                if old_hash is None:
                    old_hash = news_hash
                    print(Fore.GREEN + "  Watching for news change…")
                    count += 1
                elif news_hash != old_hash:
                    print(Fore.CYAN + f"\n  [!] News updated!")
                    motds = (data.get("data") or {}).get("motds") or []
                    if motds:
                        entry   = motds[0]
                        title   = entry.get("title", "")
                        body    = entry.get("body", "")
                        img_url = entry.get("tileImage", "")

                        tweet_text = f"#Fortnite News Update: {title}\n\n'{body}'\n[{name}]"

                        if img_url and tw.ready:
                            try:
                                img_resp = requests.get(img_url, timeout=15)
                                img_resp.raise_for_status()
                                img_path = "cache/brnews.png"
                                with open(img_path, "wb") as f:
                                    f.write(img_resp.content)
                                tw.tweet_with_media(img_path, tweet_text)
                                print(Fore.GREEN + "  Tweeted news update!")
                            except Exception as e:
                                print(Fore.RED + f"  Failed to tweet news image: {e}")
                                if tw.ready:
                                    tw.tweet(tweet_text)
                        elif tw.ready:
                            tw.tweet(tweet_text)
                        else:
                            print(Fore.YELLOW + f"  (Twitter not configured)\n{tweet_text}")
                    old_hash = news_hash
                else:
                    count += 1
                    print(Fore.GREEN + f"  Watching… ({count})", end="\r")
            time.sleep(delay)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nNews watcher stopped.")


# ── emergency notices ─────────────────────────────────────────────────────────

def watch_notices(cfg: dict, tw) -> None:
    """Watch for changes in Fortnite's emergency notices and tweet them."""
    delay = _cfg_delay(cfg)
    name  = cfg["name"]
    url   = NOTICES_API

    print(Fore.CYAN + f"\n-- Notices Watcher --  (delay={delay}s)")
    print(Fore.YELLOW + "Press Ctrl-C to stop.\n")

    old_data = None
    count    = 0

    try:
        while True:
            data = _get_json(url)
            if data:
                status = data.get("status") or {}
                current = json.dumps(status, sort_keys=True)
                if old_data is None:
                    old_data = current
                    print(Fore.GREEN + "  Watching for notice changes…")
                elif current != old_data:
                    print(Fore.CYAN + "\n  [!] Notice changed!")
                    indicator = status.get("indicator", "unknown")
                    msg       = status.get("description", "Status changed")
                    tweet_text = f"New #Fortnite notice:\n{msg}\n[{name}]"
                    if tw.ready:
                        tw.tweet(tweet_text)
                        print(Fore.GREEN + "  Tweeted notice!")
                    else:
                        print(Fore.YELLOW + f"  (Twitter not configured)\n{tweet_text}")
                    old_data = current
                else:
                    count += 1
                    print(Fore.GREEN + f"  Watching… ({count})", end="\r")
            time.sleep(delay)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nNotices watcher stopped.")


# ── staging servers ───────────────────────────────────────────────────────────

def watch_staging(cfg: dict, tw) -> None:
    """
    Poll the Epic Games staging server endpoint.
    Tweets when the version changes (indicating an upcoming patch).
    """
    delay = _cfg_delay(cfg)
    name  = cfg["name"]

    print(Fore.CYAN + f"\n-- Staging Server Watcher --  (delay={delay}s)")
    print(Fore.YELLOW + "Press Ctrl-C to stop.\n")

    old_version = None
    count       = 0

    try:
        while True:
            data = _get_json(STAGING_URL, timeout=10)
            if data:
                version = data.get("version", "")
                if old_version is None:
                    old_version = version
                    print(Fore.GREEN + f"  Current staging version: {version}")
                elif version != old_version:
                    print(Fore.CYAN + f"\n  [!] Staging updated: {old_version} → {version}")
                    tweet_text = (
                        f"#Fortnite Version Update:\n\n"
                        f"Patch v{version} has been pushed to the pre-release staging servers.\n"
                        f"Epic is testing this update — expect a release within the coming week(s).\n"
                        f"[{name}]"
                    )
                    if tw.ready:
                        tw.tweet(tweet_text)
                        print(Fore.GREEN + "  Tweeted staging update!")
                    else:
                        print(Fore.YELLOW + f"  (Twitter not configured)\n{tweet_text}")
                    old_version = version
                else:
                    count += 1
                    print(Fore.GREEN + f"  Watching… ({count})", end="\r")
            else:
                print(Fore.YELLOW + "  Staging server unreachable — retrying…")
            time.sleep(delay)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nStaging watcher stopped.")
