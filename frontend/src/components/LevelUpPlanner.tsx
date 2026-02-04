import { useMemo, useState } from 'react'
import { StatPlan } from '../services/gameAPI'
import styles from './LevelUpPlanner.module.css'

interface LevelUpPlannerProps {
  pointsAvailable: number
  onConfirm: (stats: StatPlan) => void
  onCancel: () => void
}

const EMPTY_STATS: StatPlan = {
  strength: 0,
  health: 0,
  stamina: 0,
  dodge: 0,
  initiative: 0,
  weaponskill: 0,
}

export function LevelUpPlanner({
  pointsAvailable,
  onConfirm,
  onCancel,
}: LevelUpPlannerProps) {
  const [stats, setStats] = useState<StatPlan>(EMPTY_STATS)

  const statRows = useMemo(
    () => [
      { key: 'strength', label: 'Strength' },
      { key: 'health', label: 'Health' },
      { key: 'stamina', label: 'Stamina' },
      { key: 'dodge', label: 'Dodge' },
      { key: 'initiative', label: 'Initiative' },
      { key: 'weaponskill', label: 'Weaponskill' },
    ] as const,
    []
  )

  const totalPoints = statRows.reduce((sum, row) => sum + stats[row.key], 0)
  const remainingPoints = pointsAvailable - totalPoints

  const updateStat = (key: keyof StatPlan, nextValue: number) => {
    const safeValue = Math.max(0, Math.floor(nextValue))
    const totalWithout = totalPoints - stats[key]
    const maxForStat = Math.max(0, pointsAvailable - totalWithout)
    const clampedValue = Math.min(safeValue, maxForStat)
    setStats((prev) => ({ ...prev, [key]: clampedValue }))
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h2>Place Your Stat Points</h2>
          <span className={styles.pointsRemaining}>
            {remainingPoints} points left
          </span>
        </div>

        <div className={styles.plannerGrid}>
          {statRows.map((row) => (
            <div key={row.key} className={styles.plannerRow}>
              <div className={styles.plannerLabel}>{row.label}</div>
              <div className={styles.plannerControls}>
                <button
                  type="button"
                  className={styles.controlButton}
                  onClick={() => updateStat(row.key, stats[row.key] - 1)}
                  disabled={stats[row.key] <= 0}
                >
                  -
                </button>
                <input
                  className={styles.statInput}
                  type="number"
                  min={0}
                  max={pointsAvailable}
                  value={stats[row.key]}
                  onChange={(event) =>
                    updateStat(row.key, Number(event.target.value))
                  }
                />
                <button
                  type="button"
                  className={styles.controlButton}
                  onClick={() => updateStat(row.key, stats[row.key] + 1)}
                  disabled={remainingPoints <= 0}
                >
                  +
                </button>
                <button
                  type="button"
                  className={styles.controlButton}
                  onClick={() => updateStat(row.key, stats[row.key] + 5)}
                  disabled={remainingPoints <= 0}
                >
                  +5
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className={styles.actions}>
          <button className={styles.secondaryButton} type="button" onClick={onCancel}>
            Go Back
          </button>
          <button
            className={styles.primaryButton}
            type="button"
            onClick={() => onConfirm(stats)}
            disabled={totalPoints <= 0 || remainingPoints < 0}
          >
            Confirm Stats
          </button>
        </div>
      </div>
    </div>
  )
}
