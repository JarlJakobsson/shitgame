import { useState } from 'react'
import { GladiatorWithEquipment, RecoveryStatus } from '../services/gameAPI'
import { EquipmentManager } from './EquipmentManager'
import styles from './GameDashboard.module.css'
import humanImg from '../assets/human.png'
import orcImg from '../assets/orc.png'
import goblinImg from '../assets/goblin.png'
import minotaurImg from '../assets/minotaur.png'
import skeletonImg from '../assets/skeleton.png'
import banditImg from '../assets/bandit.png'
import darkKnightImg from '../assets/darkknight.png'
import slimeImg from '../assets/slime.png'

interface GameDashboardProps {
  gladiator: GladiatorWithEquipment
  onTrain: () => void
  onFight: () => void
  onRandomBattle: () => void
  onOpenGladiators: () => void
  onOpenChallenges: () => void
  onOpenHistory: () => void
  onOpenAttributes: () => void
  onLogout: () => void
  loading: boolean
  queuedForRandomBattle: boolean
  recoveryStatus: RecoveryStatus | null
  onGladiatorUpdate: (gladiator: GladiatorWithEquipment) => void
}

export function GameDashboard({
  gladiator,
  onTrain,
  onFight,
  onRandomBattle,
  onOpenGladiators,
  onOpenChallenges,
  onOpenHistory,
  onOpenAttributes,
  onLogout,
  loading,
  queuedForRandomBattle,
  recoveryStatus,
  onGladiatorUpdate,
}: GameDashboardProps) {
  const XP_POWER = 1.4818954149270105
  const XP_COEFF = 54.81592736945923

  const healthPercentage = (gladiator.current_health / gladiator.max_health) * 100
  const xpToNext = Math.max(1, Math.round(XP_COEFF * Math.pow(Math.max(1, gladiator.level), XP_POWER)))
  const xpProgressPercentage = Math.max(0, Math.min(100, (gladiator.experience / xpToNext) * 100))

  const recoveryInterval = recoveryStatus?.interval_seconds ?? 60
  const recoverySeconds = recoveryStatus?.seconds_until_next_tick ?? recoveryInterval
  const recoveryProgressPercentage = Math.max(
    0,
    Math.min(100, ((recoveryInterval - recoverySeconds) / recoveryInterval) * 100),
  )
  const recoveryMinutesPart = Math.floor(recoverySeconds / 60)
  const recoverySecondsPart = recoverySeconds % 60
  const recoveryCountdown = `${String(recoveryMinutesPart).padStart(2, '0')}:${String(recoverySecondsPart).padStart(2, '0')}`
  const raceKey = gladiator.race.toLowerCase()
  const portraitMap: Record<string, string> = {
    human: humanImg,
    orc: orcImg,
    goblin: goblinImg,
    minotaur: minotaurImg,
    skeleton: skeletonImg,
    bandit: banditImg,
    'dark knight': darkKnightImg,
    slime: slimeImg,
  }
  const portrait = portraitMap[raceKey]
  const [showEquipment, setShowEquipment] = useState(false)

  return (
    <div className={styles.container}>
      <div className={`${styles.dashboard} ${loading ? styles.dashboardLoading : ''}`}>
        <div className={styles.header}>
          <div>
            <div className={styles.name}>{gladiator.name}</div>
            <div className={styles.subtitle}>{gladiator.race} Gladiator</div>
          </div>
          <button className={styles.logoutBtn} onClick={onLogout}>
            Logout
          </button>
        </div>

        <div className={styles.mainGrid}>
          <div className={styles.overview}>
            <div className={styles.heroRow}>
              <div className={styles.portraitCard}>
                {portrait ? (
                  <img src={portrait} alt={gladiator.race} className={styles.portrait} />
                ) : (
                  <div className={styles.portraitFallback}>?</div>
                )}
              </div>

              <div className={styles.statusCard}>
                <div className={styles.statRow}>
                  <span>Race</span>
                  <span>{gladiator.race}</span>
                </div>
                <div className={styles.statRow}>
                  <span>Level</span>
                  <span>{gladiator.level}</span>
                </div>
                <div className={styles.statRow}>
                  <span>Experience</span>
                  <span>{gladiator.experience}</span>
                </div>
                <div className={styles.statRow}>
                  <span>Gold</span>
                  <span>{'\uD83D\uDCB0'} {gladiator.gold}</span>
                </div>
                {gladiator.stat_points > 0 && (
                  <div className={styles.statRow}>
                    <span>Unspent</span>
                    <span className={styles.unspent}>{gladiator.stat_points} pts</span>
                  </div>
                )}

                <div className={styles.progressBlock}>
                  <div className={styles.progressHeader}>
                    <span>XP Progress</span>
                    <span>{gladiator.experience} / {xpToNext}</span>
                  </div>
                  <div className={styles.progressTrack}>
                    <div
                      className={styles.progressFillXp}
                      style={{ width: `${xpProgressPercentage}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className={styles.healthCard}>
                <div className={styles.healthHeader}>
                  <span>HP</span>
                  <span className={styles.healthValue}>
                    {gladiator.current_health} / {gladiator.max_health}
                  </span>
                </div>
                <div className={styles.barContainer}>
                  <div
                    className={styles.bar}
                    style={{ width: `${healthPercentage}%` }}
                  />
                </div>
                <div className={styles.progressBlock}>
                  <div className={styles.progressHeader}>
                    <span>Recovery</span>
                    <span>{recoveryCountdown}</span>
                  </div>
                  <div className={styles.progressTrack}>
                    <div
                      className={styles.progressFillRecovery}
                      style={{ width: `${recoveryProgressPercentage}%` }}
                    />
                  </div>
                </div>
                <div className={styles.recoveryNote}>
                  +33% HP when timer hits 00:00
                </div>
              </div>
            </div>

            <div className={styles.record}>
              <div className={styles.recordItem}>
                <span>Wins</span>
                <strong>{gladiator.wins}</strong>
              </div>
              <div className={styles.recordItem}>
                <span>Losses</span>
                <strong>{gladiator.losses}</strong>
              </div>
            </div>
          </div>

          <div className={styles.actionsPanel}>
            <div className={styles.actionsHeader}>Actions</div>
            <div className={styles.actions}>
              <button
                className={styles.primaryButton}
                onClick={onOpenAttributes}
                disabled={loading}
              >
                {gladiator.stat_points > 0 ? `Attributes (${gladiator.stat_points})` : 'Attributes'}
              </button>
              <button
                className={styles.button}
                onClick={onTrain}
                disabled={loading || gladiator.gold < 10}
              >
                {gladiator.gold < 10 ? 'Train (Need 10 Gold)' : 'Train (10 Gold)'}
              </button>
              <button
                className={styles.primaryButton}
                onClick={onFight}
                disabled={loading}
              >
                Fight in Arena
              </button>
              <button
                className={styles.primaryButton}
                onClick={onRandomBattle}
                disabled={loading || queuedForRandomBattle}
              >
                {queuedForRandomBattle ? 'Queued for Random Battle...' : 'Random Battle'}
              </button>
              <button
                className={styles.primaryButton}
                onClick={onOpenGladiators}
                disabled={loading}
              >
                Gladiators
              </button>
              <button
                className={styles.primaryButton}
                onClick={onOpenChallenges}
                disabled={loading}
              >
                Challenges
              </button>
              <button
                className={styles.primaryButton}
                onClick={onOpenHistory}
                disabled={loading}
              >
                History
              </button>
              <button
                className={styles.button}
                onClick={() => setShowEquipment(true)}
                disabled={loading}
              >
                Equipment
              </button>
            </div>
          </div>
        </div>
      </div>

      {showEquipment && (
        <EquipmentManager
          gladiator={gladiator}
          onGladiatorUpdate={onGladiatorUpdate}
          onClose={() => setShowEquipment(false)}
        />
      )}
    </div>
  )
}
