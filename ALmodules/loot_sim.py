"""
loot_sim.py — Loot Pool Simulator logic (no GUI).

Provides container presets, weighted simulation, and CSV export.
"""

from __future__ import annotations

import csv
import os
import random
from typing import Optional

# ── Container rarity weights ──────────────────────────────────────────────────
# {rarity: weight}  —  higher weight = more likely to drop
CONTAINER_PRESETS: dict[str, dict[str, int]] = {
    "Floor Loot":   {"common": 45, "uncommon": 30, "rare": 15, "epic":  7, "legendary":  3},
    "Common Chest": {"common": 35, "uncommon": 35, "rare": 20, "epic":  8, "legendary":  2},
    "Rare Chest":   {"common": 10, "uncommon": 25, "rare": 35, "epic": 20, "legendary": 10},
    "Epic Chest":   {"common":  0, "uncommon": 10, "rare": 30, "epic": 40, "legendary": 20},
    "Supply Drop":  {"common":  0, "uncommon":  5, "rare": 20, "epic": 40, "legendary": 35},
    "Boss Chest":   {"common":  0, "uncommon":  0, "rare": 10, "epic": 30, "legendary": 60},
}

CONTAINER_NAMES: list[str] = list(CONTAINER_PRESETS.keys())

RARITIES: list[str] = ["common", "uncommon", "rare", "epic", "legendary"]


def simulate(
    weapon_pool: list[dict],
    rarity_weights: dict[str, int],
    count: int,
) -> list[dict]:
    """
    Randomly pick `count` weapons from `weapon_pool` weighted by rarity.

    Parameters
    ----------
    weapon_pool     : List of weapon dicts (each has a "rarity" key)
    rarity_weights  : {rarity_string: int weight}  — 0 = excluded
    count           : Number of drops to simulate

    Returns
    -------
    list[dict]  — May contain duplicates; reflects a real drop sequence.
                  Returns [] if pool is empty or all weights are zero.
    """
    if not weapon_pool or count <= 0:
        return []

    weights = [
        max(0, rarity_weights.get((w.get("rarity") or "common").lower(), 0))
        for w in weapon_pool
    ]

    if sum(weights) == 0:
        return []

    return random.choices(weapon_pool, weights=weights, k=count)


def export_csv(results: list[dict], out_path: str) -> str:
    """
    Write simulation results to a CSV file.

    Parameters
    ----------
    results  : List of weapon dicts from simulate()
    out_path : Destination file path (.csv)

    Returns
    -------
    str — The resolved out_path
    """
    os.makedirs(
        os.path.dirname(out_path) if os.path.dirname(out_path) else ".",
        exist_ok=True,
    )

    fieldnames = [
        "displayName", "rarity", "category",
        "damagePerBullet", "firingRate", "reloadTime", "clipSize",
        "ammoType", "id",
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in results:
            stats = item.get("stats") or {}
            row = {k: item.get(k, "") for k in fieldnames}
            row["damagePerBullet"] = stats.get("damagePerBullet", "")
            row["firingRate"]      = stats.get("firingRate", "")
            row["reloadTime"]      = stats.get("reloadTime", "")
            row["clipSize"]        = stats.get("clipSize", "")
            writer.writerow(row)

    return out_path
