import { Gladiator } from '../services/gameAPI';
import styles from './GameDashboard.module.css';

interface GameDashboardProps {
  gladiator: Gladiator;
  onTrain: () => void;
  onFight: () => void;
  onLogout: () => void;
  loading: boolean;
}

export function GameDashboard({
  gladiator,
  onTrain,
  onFight,
  onLogout,
  loading,
}: GameDashboardProps) {
  const healthPercentage = (gladiator.current_health / gladiator.max_health) * 100;

  return (
    <div className={styles.container}>
      <div className={styles.dashboard}>
        <div className={styles.header}>
          <h1>{gladiator.name}</h1>
          <button className={styles.logoutBtn} onClick={onLogout}>
            Logout
          </button>
        </div>

        <div className={styles.stats}>
          <div className={styles.statRow}>
            <span>Race:</span>
            <span>{gladiator.race}</span>
          </div>
          <div className={styles.statRow}>
            <span>Level:</span>
            <span>{gladiator.level}</span>
          </div>
          <div className={styles.statRow}>
            <span>Experience:</span>
            <span>{gladiator.experience}</span>
          </div>
          <div className={styles.statRow}>
            <span>Gold:</span>
            <span>💰 {gladiator.gold}</span>
          </div>
        </div>

        <div className={styles.healthBar}>
          <div className={styles.label}>Health</div>
          <div className={styles.barContainer}>
            <div
              className={styles.bar}
              style={{ width: `${healthPercentage}%` }}
            />
          </div>
          <div className={styles.value}>
            {gladiator.current_health} / {gladiator.max_health}
          </div>
        </div>

        <div className={styles.attributes}>
          <div className={styles.attribute}>
            <span>🗡️</span>
            <span>Weaponskill: {gladiator.weaponskill}</span>
          </div>
          <div className={styles.attribute}>
            <span>🚦</span>
            <span>Initiative: {gladiator.initiative}</span>
          </div>
          <div className={styles.attribute}>
            <span>💪</span>
            <span>Strength: {gladiator.strength}</span>
          </div>
          <div className={styles.attribute}>
            <span>⚡</span>
            <span>Agility: {gladiator.agility}</span>
          </div>
          <div className={styles.attribute}>
            <span>🌀</span>
            <span>Dodge: {gladiator.agility * 2}%</span>
          </div>
          <div className={styles.attribute}>
            <span>💨</span>
            <span>Stamina: {gladiator.stamina}</span>
          </div>
        </div>

        <div className={styles.record}>
          <div>Wins: <strong>{gladiator.wins}</strong></div>
          <div>Losses: <strong>{gladiator.losses}</strong></div>
        </div>

        <div className={styles.actions}>
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
        </div>
      </div>
    </div>
  );
}
