import { useEffect, useMemo, useState } from 'react';
import { Race, StatPlan } from '../services/gameAPI';
import styles from './RaceDetails.module.css';
import humanImg from '../assets/human.png';
import orcImg from '../assets/orc.png';
import goblinImg from '../assets/goblin.png';
import minotaurImg from '../assets/minotaur.png';
import skeletonImg from '../assets/skeleton.png';

interface RaceDetailsProps {
  raceName: string;
  race: Race;
  initialStats: StatPlan;
  onConfirm: (stats: StatPlan) => void;
  onBack: () => void;
}

const raceImages: Record<string, string> = {
  human: humanImg,
  orc: orcImg,
  goblin: goblinImg,
  minotaur: minotaurImg,
  skeleton: skeletonImg,
};

export function RaceDetails({ raceName, race, initialStats, onConfirm, onBack }: RaceDetailsProps) {
  const maxPoints = 150;
  const [stats, setStats] = useState<StatPlan>(initialStats);
  const raceKey = raceName.toLowerCase();
  const raceImage = raceImages[raceKey];

  useEffect(() => {
    setStats(initialStats);
  }, [initialStats, raceName]);

  const statRows = useMemo(
    () => [
      { key: 'strength', label: 'Strength' },
      { key: 'health', label: 'Health' },
      { key: 'stamina', label: 'Stamina' },
      { key: 'agility', label: 'Agility' },
      { key: 'initiative', label: 'Initiative' },
      { key: 'weaponskill', label: 'Weaponskill' },
    ] as const,
    []
  );

  const totalPoints = statRows.reduce((sum, row) => sum + stats[row.key], 0);
  const remainingPoints = maxPoints - totalPoints;

  const updateStat = (key: keyof StatPlan, nextValue: number) => {
    const safeValue = Math.max(0, Math.floor(nextValue));
    const totalWithout = totalPoints - stats[key];
    const maxForStat = Math.max(0, maxPoints - totalWithout);
    const clampedValue = Math.min(safeValue, maxForStat);
    setStats(prev => ({ ...prev, [key]: clampedValue }));
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h2>{raceName}</h2>
          <p className={styles.subtitle}>Know your strengths before entering the arena.</p>
        </div>

        <div className={styles.topGrid}>
          <div className={styles.imageGrid}>
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={`${raceName}-image-${index}`} className={styles.imageCard}>
                {raceImage && (
                  <img className={styles.image} src={raceImage} alt={raceName} />
                )}
              </div>
            ))}
          </div>
          <div className={styles.loreCard}>
            <div className={styles.infoGrid}>
              <div className={styles.section}>
                <h3>Overview</h3>
                <p>{race.description}</p>
              </div>
              <div className={styles.section}>
                <h3>Origin</h3>
                <p>{race.origin || 'Unknown lands and forgotten myths.'}</p>
              </div>
              <div className={styles.section}>
                <h3>Specialty</h3>
                <p>{race.specialty || 'Balanced combat and survival.'}</p>
              </div>
            </div>
          </div>
        </div>

        <div className={styles.planner}>
          <div className={styles.plannerHeader}>
            <h3>Stat Planner</h3>
            <span className={styles.pointsRemaining}>
              {remainingPoints} points left
            </span>
          </div>
          <div className={styles.plannerGrid}>
            {statRows.map(row => (
              <div key={row.key} className={styles.plannerRow}>
                <span className={styles.plannerLabel}>{row.label}</span>
                <div className={styles.plannerControls}>
                  <button
                    type="button"
                    className={styles.controlButton}
                    onClick={() => updateStat(row.key, stats[row.key] - 1)}
                    disabled={stats[row.key] <= 0}
                  >
                    <span className={styles.controlButtonLabel}>-</span>
                  </button>
                  <input
                    className={styles.statInput}
                    type="number"
                    min={0}
                    max={maxPoints}
                    value={stats[row.key]}
                    onChange={event => updateStat(row.key, Number(event.target.value))}
                  />
                  <button
                    type="button"
                    className={styles.controlButton}
                    onClick={() => updateStat(row.key, stats[row.key] + 1)}
                    disabled={remainingPoints <= 0}
                  >
                    <span className={styles.controlButtonLabel}>+</span>
                  </button>
                  <button
                    type="button"
                    className={styles.controlButton}
                    onClick={() => updateStat(row.key, stats[row.key] + 5)}
                    disabled={remainingPoints <= 0}
                  >
                    <span className={styles.controlButtonLabel}>+5</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.actions}>
          <button className={styles.secondaryButton} type="button" onClick={onBack}>
            Go Back
          </button>
          <button className={styles.primaryButton} type="button" onClick={() => onConfirm(stats)}>
            Confirm Race
          </button>
        </div>
      </div>
    </div>
  );
}
