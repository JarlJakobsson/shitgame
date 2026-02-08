import { useMemo, useState } from 'react'
import { GladiatorWithEquipment, Race, StatPlan } from '../services/gameAPI'
import styles from './LevelUpPlanner.module.css'

interface LevelUpPlannerProps {
  gladiator: GladiatorWithEquipment
  race: Race | null
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
  gladiator,
  race,
  pointsAvailable,
  onConfirm,
  onCancel,
}: LevelUpPlannerProps) {
  const [stats, setStats] = useState<StatPlan>(EMPTY_STATS)

  const statRows = useMemo(
    () => [
      { key: 'strength', label: 'Strength' },
      { key: 'health', label: 'Vitality' },
      { key: 'stamina', label: 'Stamina' },
      { key: 'dodge', label: 'Dodge' },
      { key: 'initiative', label: 'Initiative' },
      { key: 'weaponskill', label: 'Weaponskill' },
    ] as const,
    []
  )
  const racialBonusMap = useMemo(() => {
    const entries = race?.racial_bonus || []
    const mapped: Record<string, string> = {}
    entries.forEach((entry) => {
      const rawKey = entry.stat.toLowerCase()
      const normalizedKey = rawKey === 'agility' ? 'dodge' : rawKey
      mapped[normalizedKey] = entry.value
    })
    return mapped
  }, [race])
  const getBonusText = (key: keyof StatPlan) => racialBonusMap[key] || '+0%'

  const totalPoints = statRows.reduce((sum, row) => sum + stats[row.key], 0)
  const remainingPoints = pointsAvailable - totalPoints
  const canAllocate = pointsAvailable > 0

  const updateStat = (key: keyof StatPlan, nextValue: number) => {
    if (!canAllocate) {
      return
    }
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
          <h2>Attributes</h2>
          <span className={styles.pointsRemaining}>
            {canAllocate ? `${remainingPoints} points left` : 'No points available'}
          </span>
        </div>

        <div className={styles.currentStats}>
          <div className={styles.currentStatRow}>
            <span>Vitality</span>
            <strong>{gladiator.vitality}</strong>
          </div>
          <div className={styles.currentStatRow}>
            <span>Strength</span>
            <strong>{gladiator.strength}</strong>
          </div>
          <div className={styles.currentStatRow}>
            <span>Stamina</span>
            <strong>{gladiator.stamina}</strong>
          </div>
          <div className={styles.currentStatRow}>
            <span>Dodge</span>
            <strong>{gladiator.dodge}</strong>
          </div>
          <div className={styles.currentStatRow}>
            <span>Initiative</span>
            <strong>{gladiator.initiative}</strong>
          </div>
          <div className={styles.currentStatRow}>
            <span>Weaponskill</span>
            <strong>{gladiator.weaponskill}</strong>
          </div>
        </div>

        <div className={styles.allocateSection}>
          <h3>Allocate Points</h3>
          {!canAllocate && (
            <p className={styles.allocateHint}>
              Earn levels to get more stat points.
            </p>
          )}
          <div className={styles.plannerGrid}>
            {statRows.map((row) => (
              <div key={row.key} className={styles.plannerRow}>
                <div className={styles.plannerLabel}>
                  {row.label} <em className={styles.bonusTag}>{getBonusText(row.key)}</em>
                </div>
                <div className={styles.plannerControls}>
                  <button
                    type="button"
                    className={styles.controlButton}
                    onClick={() => updateStat(row.key, stats[row.key] - 1)}
                    disabled={!canAllocate || stats[row.key] <= 0}
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
                    disabled={!canAllocate}
                  />
                  <button
                    type="button"
                    className={styles.controlButton}
                    onClick={() => updateStat(row.key, stats[row.key] + 1)}
                    disabled={!canAllocate || remainingPoints <= 0}
                  >
                    +
                  </button>
                  <button
                    type="button"
                    className={styles.controlButton}
                    onClick={() => updateStat(row.key, stats[row.key] + 5)}
                    disabled={!canAllocate || remainingPoints <= 0}
                  >
                    +5
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.actions}>
          <button className={styles.secondaryButton} type="button" onClick={onCancel}>
            Go Back
          </button>
          <button
            className={styles.primaryButton}
            type="button"
            onClick={() => onConfirm(stats)}
            disabled={!canAllocate || totalPoints <= 0 || remainingPoints < 0}
          >
            Confirm Attributes
          </button>
        </div>
      </div>
    </div>
  )
}
