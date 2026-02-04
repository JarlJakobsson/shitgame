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
  const prosConsByRace: Record<string, { pros: string[]; cons: string[] }> = {
    human: {
      pros: ['Jack of all traits'],
      cons: ['Jack of all traits'],
    },
  };
  const raceProsCons = prosConsByRace[raceKey];
  const bonusIcons: Record<string, string> = {
    strength: '\uD83D\uDCAA',
    health: '\u2764\uFE0F',
    stamina: '\uD83D\uDCA8',
    agility: '\u26A1',
    initiative: '\uD83C\uDFC3',
    weaponskill: '\uD83D\uDDE1\uFE0F',
  };

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

  const racialBonusMap = useMemo(() => {
    const entries = race.racial_bonus || [];
    const mapped: Record<string, string> = {};
    entries.forEach((entry) => {
      mapped[entry.stat.toLowerCase()] = entry.value;
    });
    return mapped;
  }, [race.racial_bonus]);

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
        <div className={styles.layoutGrid}>
          <div className={`${styles.sideCard} ${styles.imageCard}`}>
            {raceImage && (
              <img className={styles.image} src={raceImage} alt={raceName} />
            )}
          </div>

          <div className={styles.centerColumn}>
            <div className={styles.header}>
              <h2>{raceName}</h2>
              <p className={styles.subtitle}>Know your strengths before entering the arena.</p>
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
              </div>

              {raceProsCons && (
                <div className={styles.prosCons}>
                  <div className={styles.prosColumn}>
                    <h3>Pros</h3>
                    {raceProsCons.pros.map((item) => (
                      <div key={`pros-${item}`} className={styles.tag}>
                        <span className={styles.proTag}>+</span>
                        {item}
                      </div>
                    ))}
                  </div>
                  <div className={styles.consColumn}>
                    <h3>Cons</h3>
                    {raceProsCons.cons.map((item) => (
                      <div key={`cons-${item}`} className={styles.tag}>
                        <span className={styles.conTag}>-</span>
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {race.racials && race.racials.length > 0 && (
                <div className={styles.racials}>
                  <h3>Racials</h3>
                  <div className={styles.racialGrid}>
                    {race.racials.map((racial, index) => (
                      <div key={`${racial.title}-${index}`} className={styles.racialCard}>
                        <h4 className={styles.racialTitle}>{racial.title}</h4>
                        <p className={styles.racialDesc}>{racial.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {race.racial_bonus && race.racial_bonus.length > 0 && (
                <div className={styles.racialBonus}>
                  <h3>Racial Bonus</h3>
                  <div className={styles.bonusGrid}>
                    {race.racial_bonus.map((bonus, index) => {
                      const key = bonus.stat.toLowerCase();
                      const icon = bonusIcons[key];
                      return (
                        <div key={`${bonus.stat}-${index}`} className={styles.bonusCard}>
                          <span className={styles.bonusStat}>
                            {icon && <span className={styles.bonusIcon}>{icon}</span>}
                            {bonus.stat}
                          </span>
                          <span className={styles.bonusValue}>{bonus.value}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
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

          <div className={`${styles.sideCard} ${styles.plannerCard}`}>
            <div className={styles.plannerHeader}>
              <h3>Stat Planner</h3>
              <span className={styles.pointsRemaining}>
                {remainingPoints} points left
              </span>
            </div>
            <div className={styles.plannerGrid}>
              {statRows.map(row => (
                <div key={row.key} className={styles.plannerRow}>
                  <div className={styles.plannerLabel}>
                    <span className={styles.plannerIcon}>{bonusIcons[row.key]}</span>
                    <span>{row.label}</span>
                    <span className={styles.plannerBonus}>
                      {racialBonusMap[row.key] || '+0%'}
                    </span>
                  </div>
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
        </div>
      </div>
    </div>
  );
}
