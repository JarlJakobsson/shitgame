import { useEffect, useState } from 'react'
import gameAPI, { FightHistoryDetail, FightHistoryEntry } from '../services/gameAPI'
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
    return (
      <div className={styles.container}>
        <div className={styles.panel}>
          <div className={styles.header}>
            <div>
              <div className={styles.title}>Battle Replay</div>
              <div className={styles.subtitle}>Combat log from this finished fight.</div>
            </div>
            <div className={styles.actions}>
              <button className={styles.button} onClick={() => setSelectedFight(null)}>
                Back to History
              </button>
              <button className={styles.button} onClick={onBack}>
                Return to Dashboard
              </button>
            </div>
          </div>

          <div className={styles.battlePanel}>
            <div className={styles.battleTitle}>
              vs {selectedFight.opponent_name}
            </div>
            <div className={styles.battleMeta}>
              {selectedFight.opponent_race} | Level {selectedFight.opponent_level} | Mode: {selectedFight.mode}
            </div>
            <div className={selectedFight.result === 'victory' ? styles.resultWin : styles.resultLoss}>
              Result: {selectedFight.result.toUpperCase()}
            </div>
            <div className={styles.log}>
              {selectedFight.battle_log.length === 0 && (
                <div className={styles.logEntry}>No battle log recorded.</div>
              )}
              {selectedFight.battle_log.map((entry, idx) => {
                const isRoundMarker = entry.startsWith('Round ')
                return (
                  <div
                    key={`${selectedFight.id}-${idx}`}
                    className={`${styles.logEntry} ${isRoundMarker ? styles.roundMarker : ''}`}
                  >
                    {entry}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
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
