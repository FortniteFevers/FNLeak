"""
FNLeak - A Fortnite cosmetic leak/datamine tool
Inspired by AutoLeak (FortniteFevers/AutoLeak)

Fixes over the original:
  - Pillow 10+ compatible (LANCZOS, textbbox, getbbox — no ANTIALIAS/getsize/textsize)
  - Tweepy v4 compatible (Client for v2 text tweets, API for v1.1 media)
  - No hard tkinter/pypresence dependency
  - All recursive error-retry loops replaced with proper while-loops
  - Deduplicated image generation logic
  - Graceful fallbacks for missing fonts/assets
"""

import requests
import time
import os
import json
import shutil
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

# ── module imports ────────────────────────────────────────────────────────────
from ALmodules.setup import ensure_directories, ensure_rarity_assets, resolve_font
from ALmodules.image_gen import generate_card, CardStyle
from ALmodules.merger import merge_icons
from ALmodules.compressor import compress_image
from ALmodules.twitter_client import TwitterClient
from ALmodules.monitors import watch_cosmetics, watch_news, watch_notices, watch_staging
from ALmodules.shop import generate_shop, watch_shop_sections

# ── config ────────────────────────────────────────────────────────────────────
SETTINGS_PATH = os.path.join("json", "settings.json")
FORTNITE_API   = "https://fortnite-api.com"
VERSION        = "1.2.0"

RARITY_COLORS = {
    "common":    "#636363",
    "uncommon":  "#31a21f",
    "rare":      "#3275c4",
    "epic":      "#7d3dba",
    "legendary": "#c2712c",
    "mythic":    "#e7c03a",
    "exotic":    "#21c5e7",
    "slurp":     "#00bcd4",
    "dc":        "#4a90d9",
    "marvel":    "#e52020",
    "starwars":  "#ffe81f",
    "icon":      "#1db954",
    "lambskin":  "#d4a574",
    "shadowfoil": "#4a4a6a",
    "frozen":    "#a8d8ea",
    "lava":      "#ff6b35",
    "dark":      "#2d1b69",
}


# ── settings loader ───────────────────────────────────────────────────────────
def load_settings() -> dict:
    defaults = {
        "name": "FNLeak",
        "footer": "#Fortnite",
        "language": "en",
        "imageFont": "BurbankBigCondensed-Black.otf",
        "sideFont": "OpenSans-Regular.ttf",
        "placeholderUrl": "https://i.imgur.com/W22Foja.png",
        "watermark": "",
        "useFeaturedIfAvailable": False,
        "iconType": "new",
        "twitAPIKey": "",
        "twitAPISecretKey": "",
        "twitAccessToken": "",
        "twitAccessTokenSecret": "",
        "tweetUpdate": False,
        "tweetAes": False,
        "TweetSearch": False,
        "MergeImages": True,
        "MergeWatermarkUrl": "",
        "AutoTweetMerged": False,
        "ShowDescOnNPCs": False,
        "ShopSections_Image": True,
        "ImageColor": "394ff7",
        "showitemsource": True,
        "CreatorCode": "",
        "apikey": "",
        "BotDelay": 30,
        "ShowValues_AtStart": False,
        "TwitterSupport": False,
    }

    try:
        with open(SETTINGS_PATH) as f:
            user = json.load(f)
        # Merge: user values override defaults
        for k, v in user.items():
            defaults[k] = v
    except FileNotFoundError:
        print(Fore.YELLOW + f"{SETTINGS_PATH} not found — using defaults. Run (reset) to create one.")
    except json.JSONDecodeError as e:
        print(Fore.RED + f"{SETTINGS_PATH} parse error: {e}")

    # Normalise boolean-strings from the old format
    for bool_key in ("useFeaturedIfAvailable", "tweetUpdate", "tweetAes",
                     "TweetSearch", "MergeImages", "AutoTweetMerged",
                     "ShowDescOnNPCs", "ShopSections_Image", "showitemsource",
                     "TwitterSupport", "ShowValues_AtStart"):
        v = defaults[bool_key]
        if isinstance(v, str):
            defaults[bool_key] = v.strip().lower() in ("true", "1", "yes")

    valid_languages = {"ar","de","en","es","es-419","fr","it","ja","ko","pl","pt-BR","ru","tr","zh-CN","zh-Hant"}
    if defaults["language"] not in valid_languages:
        defaults["language"] = "en"

    valid_icon_types = {"standard", "clean", "new", "cataba", "large"}
    if defaults["iconType"] not in valid_icon_types:
        defaults["iconType"] = "new"

    return defaults


# ── helpers ───────────────────────────────────────────────────────────────────
def get_image_url(item: dict, use_featured: bool) -> str:
    imgs = item.get("images", {})
    if use_featured and imgs.get("featured"):
        return imgs["featured"]
    return imgs.get("icon") or "https://i.ibb.co/KyvMydQ/do-Not-Delete.png"


def delete_icons():
    try:
        shutil.rmtree("icons")
    except FileNotFoundError:
        pass
    os.makedirs("icons", exist_ok=True)


def get_version_label(build: str) -> str:
    """Extract human-readable version from a build string like ++Fortnite+Release-28.10-CL-..."""
    try:
        return build.split("++Fortnite+Release-")[1].split("-CL-")[0]
    except (IndexError, AttributeError):
        return build or "Unknown"


# ── core feature functions ────────────────────────────────────────────────────
def cmd_generate_cosmetics(cfg: dict, tw: TwitterClient):
    """Generate card images for every new cosmetic in the latest update."""
    lang        = cfg["language"]
    icon_type   = cfg["iconType"]
    use_feat    = cfg["useFeaturedIfAvailable"]
    watermark   = cfg["watermark"]
    font_main   = resolve_font(cfg["imageFont"])
    font_side   = resolve_font(cfg["sideFont"])
    merge_wm    = cfg["MergeWatermarkUrl"]
    auto_tweet  = cfg["AutoTweetMerged"]
    name_label  = cfg["name"]
    do_merge    = cfg["MergeImages"]

    print(Fore.CYAN + f"\nFetching new cosmetics (language={lang}, iconType={icon_type})...")
    try:
        resp = requests.get(f"{FORTNITE_API}/v2/cosmetics/new", params={"language": lang}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(Fore.RED + f"API error: {e}")
        return

    data  = resp.json()["data"]
    items = data["items"]["br"]
    build = get_version_label(data.get("build", ""))
    print(Fore.GREEN + f"Patch {build} — {len(items)} new cosmetics\n")

    delete_icons()
    start = time.time()
    ok = 0
    for idx, item in enumerate(items, 1):
        item_id = item.get("id", "unknown")
        try:
            url = get_image_url(item, use_feat)
            out_path = f"icons/{item_id}.png"
            generate_card(
                item=item,
                icon_url=url,
                out_path=out_path,
                icon_type=icon_type,
                font_main=font_main,
                font_side=font_side,
                watermark=watermark,
                show_source=cfg["showitemsource"],
                build=build,
            )
            ok += 1
            pct = round(idx / len(items) * 100)
            print(Fore.CYAN + f"  [{idx}/{len(items)} {pct}%] {item_id}")
        except Exception as e:
            print(Fore.YELLOW + f"  Skipped {item_id}: {e}")

    elapsed = round(time.time() - start, 2)
    print(Fore.GREEN + f"\nGenerated {ok}/{len(items)} cards in {elapsed}s")

    if do_merge and ok > 0:
        print("\nMerging images...")
        merged_path = merge_icons("icons", "merged/merge.jpg", watermark_url=merge_wm)
        print(Fore.GREEN + f"Saved merged → {merged_path}")

        if auto_tweet and tw.ready:
            tweet_text = f"[{name_label}] Found {ok} leaked cosmetics from Patch {build}."
            _tweet_media(tw, merged_path, tweet_text)


def cmd_search_cosmetic(cfg: dict, tw: TwitterClient):
    """Search for a single cosmetic by name or ID and generate its card."""
    lang      = cfg["language"]
    icon_type = cfg["iconType"]
    use_feat  = cfg["useFeaturedIfAvailable"]
    watermark = cfg["watermark"]
    font_main = resolve_font(cfg["imageFont"])
    font_side = resolve_font(cfg["sideFont"])
    name_label = cfg["name"]
    tweet_it  = cfg["TweetSearch"]

    while True:
        query = input(Fore.GREEN + "\nEnter cosmetic name (or ID: prefix for exact ID, or 'back'): ").strip()
        if query.lower() in ("back", "exit", ""):
            return

        if query.startswith("ID:"):
            params = {"language": lang, "id": query[3:].strip()}
        else:
            params = {"language": lang, "name": query}

        try:
            resp = requests.get(f"{FORTNITE_API}/v2/cosmetics/br/search", params=params, timeout=15)
        except requests.RequestException as e:
            print(Fore.RED + f"Request failed: {e}")
            continue

        if resp.status_code == 404:
            print(Fore.RED + "Not found. Try again.")
            continue

        item = resp.json().get("data")
        if not item:
            print(Fore.RED + "No result.")
            continue

        item_id  = item["id"]
        out_path = f"icons/{item_id}.png"
        url      = get_image_url(item, use_feat)

        try:
            generate_card(
                item=item,
                icon_url=url,
                out_path=out_path,
                icon_type=icon_type,
                font_main=font_main,
                font_side=font_side,
                watermark=watermark,
                show_source=cfg["showitemsource"],
            )
        except Exception as e:
            print(Fore.RED + f"Card generation failed: {e}")
            continue

        print(Fore.GREEN + f"Saved → {out_path}")

        # Show the image (cross-platform)
        try:
            from PIL import Image
            Image.open(out_path).show()
        except Exception:
            pass

        if tweet_it and tw.ready:
            confirm = input("Tweet this? (y/n): ").strip().lower()
            if confirm == "y":
                item_name   = item.get("name", item_id)
                item_type   = item.get("type", {}).get("displayValue", "")
                item_rarity = item.get("rarity", {}).get("displayValue", "")
                item_desc   = item.get("description", "")
                intro       = item.get("introduction", {}) or {}
                season      = intro.get("season", "?")
                text = (f"[{name_label}] {item_name} ({item_type})\n"
                        f"Rarity: {item_rarity}\n{item_desc}\n"
                        f"Introduced Season {season}")
                _tweet_media(tw, out_path, text)


def cmd_set_search(cfg: dict, tw: TwitterClient):
    """Generate cards for all cosmetics in a named set."""
    lang       = cfg["language"]
    icon_type  = cfg["iconType"]
    use_feat   = cfg["useFeaturedIfAvailable"]
    watermark  = cfg["watermark"]
    font_main  = resolve_font(cfg["imageFont"])
    font_side  = resolve_font(cfg["sideFont"])
    merge_wm   = cfg["MergeWatermarkUrl"]
    auto_tweet = cfg["AutoTweetMerged"]
    name_label = cfg["name"]
    do_merge   = cfg["MergeImages"]

    set_name = input(Fore.GREEN + "\nEnter set name: ").strip()
    if not set_name:
        return

    try:
        resp = requests.get(f"{FORTNITE_API}/v2/cosmetics/br/search/all",
                            params={"set": set_name, "language": lang}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(Fore.RED + f"API error: {e}")
        return

    items = resp.json().get("data", [])
    if not items:
        print(Fore.RED + "Set not found or empty.")
        return

    delete_icons()
    print(Fore.GREEN + f"Found {len(items)} items in set '{set_name}'\n")
    ok = 0
    for idx, item in enumerate(items, 1):
        item_id = item.get("id", "unknown")
        try:
            url = get_image_url(item, use_feat)
            generate_card(
                item=item,
                icon_url=url,
                out_path=f"icons/{item_id}.png",
                icon_type=icon_type,
                font_main=font_main,
                font_side=font_side,
                watermark=watermark,
                show_source=cfg["showitemsource"],
            )
            ok += 1
            print(Fore.CYAN + f"  [{idx}/{len(items)}] {item_id}")
        except Exception as e:
            print(Fore.YELLOW + f"  Skipped {item_id}: {e}")

    print(Fore.GREEN + f"\nGenerated {ok} cards.")

    if do_merge and ok > 0:
        merged_path = merge_icons("icons", "merged/merge.jpg", watermark_url=merge_wm)
        print(Fore.GREEN + f"Saved merged → {merged_path}")

        if auto_tweet and tw.ready:
            text = f"[{name_label}] Set '{set_name}' — {ok} cosmetics."
            _tweet_media(tw, merged_path, text)


def cmd_pak_search(cfg: dict, tw: TwitterClient):
    """Generate cards for all cosmetics in a dynamic pak ID."""
    lang       = cfg["language"]
    icon_type  = cfg["iconType"]
    use_feat   = cfg["useFeaturedIfAvailable"]
    watermark  = cfg["watermark"]
    font_main  = resolve_font(cfg["imageFont"])
    font_side  = resolve_font(cfg["sideFont"])
    merge_wm   = cfg["MergeWatermarkUrl"]
    name_label = cfg["name"]
    do_merge   = cfg["MergeImages"]

    pak_id = input(Fore.GREEN + "\nEnter dynamic pak ID: ").strip()
    if not pak_id:
        return

    try:
        resp = requests.get(f"{FORTNITE_API}/v2/cosmetics/br/search/all",
                            params={"dynamicPakId": pak_id, "language": lang}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(Fore.RED + f"API error: {e}")
        return

    items = resp.json().get("data", [])
    if not items:
        print(Fore.RED + "Pak not found or empty.")
        return

    delete_icons()
    print(Fore.GREEN + f"Found {len(items)} items in pak\n")
    ok = 0
    for idx, item in enumerate(items, 1):
        item_id = item.get("id", "unknown")
        try:
            url = get_image_url(item, use_feat)
            generate_card(
                item=item,
                icon_url=url,
                out_path=f"icons/{item_id}.png",
                icon_type=icon_type,
                font_main=font_main,
                font_side=font_side,
                watermark=watermark,
                show_source=cfg["showitemsource"],
            )
            ok += 1
            print(Fore.CYAN + f"  [{idx}/{len(items)}] {item_id}")
        except Exception as e:
            print(Fore.YELLOW + f"  Skipped {item_id}: {e}")

    print(Fore.GREEN + f"\nGenerated {ok} cards.")

    if do_merge and ok > 0:
        merged_path = merge_icons("icons", "merged/merge.jpg", watermark_url=merge_wm)
        print(Fore.GREEN + f"Saved merged → {merged_path}")

        if cfg["AutoTweetMerged"] and tw.ready:
            text = f"[{name_label}] Pak {pak_id} — {ok} cosmetics."
            _tweet_media(tw, merged_path, text)


def cmd_tweet_aes(cfg: dict, tw: TwitterClient):
    try:
        resp = requests.get(f"{FORTNITE_API}/v2/aes", timeout=10)
        resp.raise_for_status()
        key   = resp.json()["data"]["mainKey"]
        build = resp.json()["data"]["build"]
        text  = f"[{cfg['name']}] Current Fortnite AES Key (build {build}):\n\n0x{key}\n\n{cfg['footer']}"
        if tw.ready:
            tw.tweet(text)
            print(Fore.GREEN + "Tweeted AES key!")
        else:
            print(Fore.YELLOW + f"Twitter not configured. AES key:\n{text}")
    except Exception as e:
        print(Fore.RED + f"Failed: {e}")


def cmd_tweet_build(cfg: dict, tw: TwitterClient):
    try:
        resp = requests.get(f"{FORTNITE_API}/v2/aes", timeout=10)
        resp.raise_for_status()
        build = resp.json()["data"]["build"]
        text  = f"[{cfg['name']}] Current Fortnite build:\n\n{build}\n\n{cfg['footer']}"
        if tw.ready:
            tw.tweet(text)
            print(Fore.GREEN + "Tweeted build!")
        else:
            print(Fore.YELLOW + f"Twitter not configured. Build:\n{text}")
    except Exception as e:
        print(Fore.RED + f"Failed: {e}")


def cmd_merge_images(cfg: dict, tw: TwitterClient):
    icon_count = len([f for f in os.listdir("icons") if f.endswith(".png")])
    if icon_count == 0:
        print(Fore.RED + "No icons to merge.")
        return
    merged_path = merge_icons("icons", "merged/merge.jpg", watermark_url=cfg["MergeWatermarkUrl"])
    print(Fore.GREEN + f"Merged {icon_count} icons → {merged_path}")

    if cfg["AutoTweetMerged"] and tw.ready:
        confirm = input("Tweet this merged image? (y/n): ").strip().lower()
        if confirm == "y":
            text = input("Tweet text: ").strip()
            _tweet_media(tw, merged_path, f"[{cfg['name']}] {text}")


def cmd_update_mode(cfg: dict, tw: TwitterClient):
    """Poll for cosmetic hash changes and auto-generate on update."""
    try:
        delay = int(cfg.get("BotDelay", 30))
    except (TypeError, ValueError):
        delay = 30
    watch_cosmetics(
        cfg=cfg,
        on_update=lambda: cmd_generate_cosmetics(cfg, tw),
        delay=delay,
        language=cfg["language"],
    )


def _tweet_media(tw: TwitterClient, path: str, text: str):
    """Try tweeting with media; compress and retry if too large."""
    try:
        tw.tweet_with_media(path, text)
        print(Fore.GREEN + "Tweeted successfully!")
    except Exception as e:
        print(Fore.YELLOW + f"First tweet attempt failed ({e}), compressing...")
        compressed = compress_image(path)
        try:
            tw.tweet_with_media(compressed, text)
            print(Fore.GREEN + "Tweeted (compressed) successfully!")
        except Exception as e2:
            print(Fore.RED + f"Tweet failed after compression: {e2}")


def cmd_reset_settings():
    confirm = input("Reset json/settings.json to defaults? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    default_settings = {
        "name": "FNLeak",
        "footer": "#Fortnite",
        "language": "en",
        "imageFont": "BurbankBigCondensed-Black.otf",
        "sideFont": "OpenSans-Regular.ttf",
        "placeholderUrl": "https://i.imgur.com/W22Foja.png",
        "watermark": "",
        "useFeaturedIfAvailable": False,
        "iconType": "new",
        "twitAPIKey": "",
        "twitAPISecretKey": "",
        "twitAccessToken": "",
        "twitAccessTokenSecret": "",
        "tweetUpdate": False,
        "tweetAes": False,
        "TweetSearch": False,
        "MergeImages": True,
        "MergeWatermarkUrl": "",
        "AutoTweetMerged": False,
        "ShowDescOnNPCs": False,
        "ShopSections_Image": True,
        "ImageColor": "394ff7",
        "showitemsource": True,
        "CreatorCode": "",
        "apikey": "",
        "BotDelay": 30,
        "ShowValues_AtStart": False,
        "TwitterSupport": False,
    }
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(default_settings, f, indent=2)
    print(Fore.GREEN + "json/settings.json reset.")


# ── banner + menu ─────────────────────────────────────────────────────────────
BANNER = Fore.CYAN + r"""
  ███████╗███╗   ██╗██╗     ███████╗ █████╗ ██╗  ██╗
  ██╔════╝████╗  ██║██║     ██╔════╝██╔══██╗██║ ██╔╝
  █████╗  ██╔██╗ ██║██║     █████╗  ███████║█████╔╝
  ██╔══╝  ██║╚██╗██║██║     ██╔══╝  ██╔══██║██╔═██╗
  ██║     ██║ ╚████║███████╗███████╗██║  ██║██║  ██╗
  ╚═╝     ╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝
""" + Style.RESET_ALL


def print_menu():
    print(Fore.GREEN + "\n- - - - - MENU - - - - -\n")
    print(Fore.RED + "- IMPORTANT -")
    print(Fore.YELLOW + "(reset)" + Fore.GREEN + " - Reset json/settings.json to defaults\n")

    print(Fore.CYAN + "- MAIN COMMANDS -")
    print(Fore.YELLOW + "(1)" + Fore.WHITE + " - Start update mode (auto-detects new cosmetics)")
    print(Fore.YELLOW + "(2)" + Fore.WHITE + " - Generate new cosmetics now")
    print(Fore.YELLOW + "(3)" + Fore.WHITE + " - Search for a single cosmetic")
    print(Fore.YELLOW + "(4)" + Fore.WHITE + " - Grab all cosmetics from a pak ID")
    print(Fore.YELLOW + "(5)" + Fore.WHITE + " - Generate Item Shop image")

    print(Fore.CYAN + "\n- OTHER COMMANDS -")
    print(Fore.WHITE + "(6)  - Tweet current Fortnite build")
    print(Fore.WHITE + "(7)  - Tweet current AES key")
    print(Fore.WHITE + "(8)  - Clear icons folder")
    print(Fore.WHITE + "(9)  - Watch BR news feed for changes")
    print(Fore.WHITE + "(10) - Merge icons in the icons folder")
    print(Fore.WHITE + "(11) - Watch shop sections for changes")
    print(Fore.WHITE + "(12) - Watch emergency notices")
    print(Fore.WHITE + "(13) - Watch staging server version")

    print(Fore.CYAN + "\n- BETA COMMANDS -")
    print(Fore.WHITE + "(15) - Search all cosmetics by set name")
    print("")


def main():
    ensure_directories()
    ensure_rarity_assets(RARITY_COLORS)

    print(BANNER)
    print(Fore.WHITE + f"  FNLeak v{VERSION}  |  fortnite-api.com\n")

    cfg = load_settings()

    if cfg.get("ShowValues_AtStart"):
        print(Fore.CYAN + "Loaded settings:")
        for k, v in cfg.items():
            if "secret" in k.lower() or "token" in k.lower() or "key" in k.lower():
                display = "***" if v else "(not set)"
            else:
                display = v
            print(f"  {k}: {display}")
        print()

    tw = TwitterClient(
        api_key=cfg["twitAPIKey"],
        api_secret=cfg["twitAPISecretKey"],
        access_token=cfg["twitAccessToken"],
        access_token_secret=cfg["twitAccessTokenSecret"],
    )

    if tw.ready:
        print(Fore.GREEN + "Twitter/X: connected\n")
    else:
        print(Fore.YELLOW + "Twitter/X: not configured (Twitter features disabled)\n")

    print_menu()

    choice = input(">> ").strip().lower()

    dispatch = {
        "reset": lambda: cmd_reset_settings(),
        "1":     lambda: cmd_update_mode(cfg, tw),
        "2":     lambda: cmd_generate_cosmetics(cfg, tw),
        "3":     lambda: cmd_search_cosmetic(cfg, tw),
        "4":     lambda: cmd_pak_search(cfg, tw),
        "5":     lambda: generate_shop(cfg, tw),
        "6":     lambda: cmd_tweet_build(cfg, tw),
        "7":     lambda: cmd_tweet_aes(cfg, tw),
        "8":     lambda: (delete_icons(), print(Fore.GREEN + "Icons folder cleared.")),
        "9":     lambda: watch_news(cfg, tw),
        "10":    lambda: cmd_merge_images(cfg, tw),
        "11":    lambda: watch_shop_sections(cfg, tw),
        "12":    lambda: watch_notices(cfg, tw),
        "13":    lambda: watch_staging(cfg, tw),
        "15":    lambda: cmd_set_search(cfg, tw),
    }

    action = dispatch.get(choice)
    if action:
        action()
    else:
        print(Fore.RED + "Invalid option.")
        time.sleep(1)
        main()


if __name__ == "__main__":
    main()
