# ============================================
# LEVELING SYSTEM
# ============================================

from __future__ import annotations

import math

# Power curve fitted so:
# level 18 -> 3999 XP to level up
# level 30 -> 8458 XP to level up
_XP_POWER = 1.466387695400268
_XP_COEFF = 57.70789704047412


def xp_to_next(level: int) -> int:
    """Return XP required to advance from the given level."""
    if level < 1:
        level = 1
    return max(1, int(round(_XP_COEFF * (level ** _XP_POWER))))


def apply_experience(gladiator, amount: int) -> dict:
    """
    Apply experience, leveling up as needed.

    Returns a dict with:
      - levels_gained
      - xp_to_next
    """
    if amount <= 0:
        return {"levels_gained": 0, "xp_to_next": xp_to_next(gladiator.level)}

    gladiator.experience += amount
    levels_gained = 0

    while True:
        required = xp_to_next(gladiator.level)
        if gladiator.experience < required:
            break
        gladiator.experience -= required
        gladiator.level += 1
        levels_gained += 1

    if levels_gained > 0:
        if not hasattr(gladiator, "stat_points"):
            gladiator.stat_points = 0
        gladiator.stat_points += levels_gained * 20

    return {"levels_gained": levels_gained, "xp_to_next": xp_to_next(gladiator.level)}
