import { useState } from 'react';
import { Race } from '../services/gameAPI';
import styles from './RaceSelection.module.css';

interface RaceSelectionProps {
  races: Record<string, Race>;
  onSelectRace: (raceName: string) => void;
}

export function RaceSelection({ races, onSelectRace }: RaceSelectionProps) {
  const [selectedRace, setSelectedRace] = useState<string | null>(null);

  const handleSelect = (raceName: string) => {
    setSelectedRace(raceName);
  };

  const handleConfirm = () => {
    if (selectedRace) {
      onSelectRace(selectedRace);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h2>Select Your Race</h2>
        <div className={styles.raceList}>
          {Object.entries(races).map(([name, stats]) => (
            <div
              key={name}
              className={`${styles.raceOption} ${selectedRace === name ? styles.selected : ''}`}
              onClick={() => handleSelect(name)}
            >
              <h3>{name}</h3>
              <p>{stats.description}</p>
              <div className={styles.stats}>
                <span>❤️ {stats.health}</span>
                <span>💪 {stats.strength}</span>
                <span>⚡ {stats.agility}</span>
              </div>
            </div>
          ))}
        </div>
        <button
          className={styles.button}
          onClick={handleConfirm}
          disabled={!selectedRace}
        >
          Confirm Selection
        </button>
      </div>
    </div>
  );
}
