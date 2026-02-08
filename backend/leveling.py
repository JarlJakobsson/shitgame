# ============================================
# LEVELING SYSTEM
# ============================================

from __future__ import annotations

# Power curve fitted so:
# level 18 -> 3999 XP to level up
# level 30 -> 8458 XP to level up
_XP_POWER = 1.4818954149270105
_XP_COEFF = 54.81592736945923


def xp_to_next(level: int) -> int:
    """Return XP required to advance from the given level."""
    if level < 1:
        raise ValueError(f"Invalid level: {level}. Level must be >= 1.")
    return max(1, int(round(_XP_COEFF * (level ** _XP_POWER))))


def apply_experience(gladiator, amount: int) -> None:
    """Apply experience with at most one level-up per reward."""
    if amount <= 0:
        return

    gladiator.experience += amount
    required = xp_to_next(gladiator.level)
    if gladiator.experience >= required:
        gladiator.experience -= required
        gladiator.level += 1
        gladiator.stat_points = getattr(gladiator, "stat_points", 0) + 20
