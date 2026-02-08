import { useEffect, useState } from 'react'
import gameAPI, { FightHistoryDetail, FightHistoryEntry } from '../services/gameAPI'
import { Arena } from './Arena'
import styles from './BattleHistory.module.css'

interface BattleHistoryProps {
  onBack: () => void
}

export function BattleHistory({ onBack }: BattleHistoryProps) {
  const [history, setHistory] = useState<FightHistoryEntry[]>([])
  const [selectedFight, setSelectedFight] = useState<FightHistoryDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [openingId, setOpeningId] = useState<number | null>(null)
  const [error, setError] = useState('')

  const loadHistory = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await gameAPI.getFightHistory()
      setHistory(data.fights)
    } catch {
      setError('Failed to load fight history.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadHistory()
  }, [])

  const openFight = async (fightId: number) => {
    setOpeningId(fightId)
    setError('')
    try {
      const detail = await gameAPI.getFightHistoryDetail(fightId)
      setSelectedFight(detail)
    } catch {
      setError('Failed to load fight details.')
    } finally {
      setOpeningId(null)
    }
  }

  if (selectedFight) {
    const battleScreen = selectedFight.battle_screen ?? {
      player: {
        name: 'You',
        race: 'Human',
        level: 0,
        current_health: 0,
        max_health: 0,
      },
      opponent: {
        name: selectedFight.opponent_name,
        race: selectedFight.opponent_race,
        level: selectedFight.opponent_level,
        current_health: 0,
        max_health: 0,
      },
      result: selectedFight.result,
      reward_gold: 0,
      reward_exp: 0,
      rounds: 0,
      battle_log: selectedFight.battle_log,
    }

    return (
      <Arena
        onBattleEnd={onBack}
        playerRace={battleScreen.player.race || 'Human'}
        replayData={{
          player_name: battleScreen.player.name,
          player_race: battleScreen.player.race || 'Human',
          opponent_name: battleScreen.opponent.name,
          opponent_race: battleScreen.opponent.race || 'Unknown',
          player_health: battleScreen.player.current_health,
          player_max_health: battleScreen.player.max_health,
          opponent_health: battleScreen.opponent.current_health,
          opponent_max_health: battleScreen.opponent.max_health,
          rounds: battleScreen.rounds,
          result: battleScreen.result,
          reward_gold: battleScreen.reward_gold,
          reward_exp: battleScreen.reward_exp,
          battle_log: battleScreen.battle_log,
        }}
      />
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.panel}>
        <div className={styles.header}>
          <div>
            <div className={styles.title}>History</div>
            <div className={styles.subtitle}>All your previous fights.</div>
          </div>
          <div className={styles.actions}>
            <button className={styles.button} onClick={() => void loadHistory()} disabled={loading}>
              Refresh
            </button>
            <button className={styles.button} onClick={onBack}>Back</button>
          </div>
        </div>

        {error && <div className={styles.error}>{error}</div>}

        {history.length === 0 ? (
          <div className={styles.empty}>No fights recorded yet.</div>
        ) : (
          <div className={styles.list}>
            {history.map((fight) => (
              <div key={fight.id} className={styles.row}>
                <div className={styles.name}>vs {fight.opponent_name}</div>
                <div className={styles.mode}>{fight.mode}</div>
                <div className={styles.line}>Race: {fight.opponent_race}</div>
                <div className={styles.line}>Level: {fight.opponent_level}</div>
                <div className={styles.line}>
                  Result:{' '}
                  <span className={fight.result === 'victory' ? styles.resultWin : styles.resultLoss}>
                    {fight.result.toUpperCase()}
                  </span>
                </div>
                {fight.created_at && (
                  <div className={styles.line}>
                    {new Date(fight.created_at).toLocaleString()}
                  </div>
                )}
                <button
                  className={styles.viewBtn}
                  disabled={openingId === fight.id}
                  onClick={() => void openFight(fight.id)}
                >
                  {openingId === fight.id ? 'Opening...' : 'Open Battle Screen'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
