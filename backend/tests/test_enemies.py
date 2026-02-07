"""
Unit tests for enemy balancing targets.
"""

from combat import Combat
from enemies import ENEMIES


def _collapse_round(stamina: int) -> int:
    remaining = stamina
    previous_required = 0
    for round_number in range(1, 100):
        required_now = Combat._required_stamina_for_round(round_number)
        drain = max(0, required_now - previous_required)
        remaining -= drain
        previous_required = required_now
        if remaining <= 0:
            return round_number
    raise AssertionError("Stamina did not collapse within expected range")


def test_enemy_stamina_targets_8_to_14_rounds():
    for enemy_name, enemy_stats in ENEMIES.items():
        collapse_round = _collapse_round(enemy_stats["stamina"])
        assert 8 <= collapse_round <= 14, (
            f"{enemy_name} stamina={enemy_stats['stamina']} collapses at round {collapse_round},"
            " expected 8-14"
        )
