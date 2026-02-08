import { useState } from 'react'
import { GladiatorWithEquipment } from '../services/gameAPI'
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
  onAllocateStats: () => void
  onLogout: () => void
  loading: boolean
  queuedForRandomBattle: boolean
  onGladiatorUpdate: (gladiator: GladiatorWithEquipment) => void
}

export function GameDashboard({
  gladiator,
  onTrain,
  onFight,
  onRandomBattle,
  onAllocateStats,
  onLogout,
  loading,
  queuedForRandomBattle,
  onGladiatorUpdate,
}: GameDashboardProps) {
  const healthPercentage = (gladiator.current_health / gladiator.max_health) * 100
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
            <div className={styles.healthNote}>
              Current HP: {gladiator.current_health}
            </div>
          </div>
        </div>

        <div className={styles.attributes}>
          <div className={styles.attribute}>
            <span>{'\u2764\uFE0F'}</span>
            <span>Vitality: {gladiator.vitality}</span>
          </div>
          <div className={styles.attribute}>
            <span>{'\uD83D\uDDE1\uFE0F'}</span>
            <span>Weaponskill: {gladiator.weaponskill}</span>
          </div>
          <div className={styles.attribute}>
            <span>{'\uD83D\uDEA6'}</span>
            <span>Initiative: {gladiator.initiative}</span>
          </div>
          <div className={styles.attribute}>
            <span>{'\uD83D\uDCAA'}</span>
            <span>Strength: {gladiator.strength}</span>
          </div>
          <div className={styles.attribute}>
            <span>{'\uD83C\uDF00'}</span>
            <span>Dodge: {gladiator.dodge}</span>
          </div>
          <div className={styles.attribute}>
            <span>{'\uD83D\uDCA8'}</span>
            <span>Stamina: {gladiator.stamina}</span>
          </div>
        </div>

        <div className={styles.record}>
          <div>Wins: <strong>{gladiator.wins}</strong></div>
          <div>Losses: <strong>{gladiator.losses}</strong></div>
        </div>

        <div className={styles.actions}>
          {gladiator.stat_points > 0 && (
            <button
              className={styles.primaryButton}
              onClick={onAllocateStats}
              disabled={loading}
            >
              New Stats ({gladiator.stat_points})
            </button>
          )}
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
            className={styles.button}
            onClick={() => setShowEquipment(true)}
            disabled={loading}
          >
            Equipment
          </button>
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
