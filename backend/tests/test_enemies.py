"""
Unit tests for enemy balancing targets.
"""

from combat import Combat
from enemies import ENEMIES


def _collapse_round(stamina: int) -> int:
    return Combat._round_capacity_from_stamina(stamina)


def test_enemy_stamina_targets_8_to_14_rounds():
    for enemy_name, enemy_stats in ENEMIES.items():
        collapse_round = _collapse_round(enemy_stats["stamina"])
        assert 8 <= collapse_round <= 14, (
            f"{enemy_name} stamina={enemy_stats['stamina']} collapses at round {collapse_round},"
            " expected 8-14"
        )
