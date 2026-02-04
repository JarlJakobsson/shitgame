import { useState } from 'react';
import { Race } from '../services/gameAPI';
import styles from './RaceSelection.module.css';
import humanImg from '../assets/human.png';
import orcImg from '../assets/orc.png';

interface RaceSelectionProps {
  races: Record<string, Race>;
  onSelectRace: (raceName: string) => void;
}

const raceImages: Record<string, string> = {
  human: humanImg,
  orc: orcImg,
};

export function RaceSelection({ races, onSelectRace }: RaceSelectionProps) {
  const [selectedRace, setSelectedRace] = useState<string | null>(null);

  // Get available race keys, normalized to lowercase
  const raceKeys = Object.keys(races).map(k => k.toLowerCase()).filter(k => k === 'human' || k === 'orc');

  const handleSelect = (raceName: string) => {
    setSelectedRace(raceName);
  };

  const handleConfirm = () => {
    if (selectedRace) {
      onSelectRace(selectedRace);
    }
  };

  if (raceKeys.length === 0) {
    return <div className={styles.container}><div>Loading races...</div></div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h2>Select Your Race</h2>
        <div className={styles.raceList}>
          {raceKeys.map(raceKey => (
            <div
              key={raceKey}
              className={`${styles.raceOption} ${selectedRace === raceKey ? styles.selected : ''}`}
              onClick={() => handleSelect(raceKey)}
            >
              <img
                src={raceImages[raceKey]}
                alt={raceKey}
                className={styles.raceImage}
              />
              <div className={styles.raceDetails}>
                <h3>{raceKey.charAt(0).toUpperCase() + raceKey.slice(1)}</h3>
                <p>{races[raceKey] ? races[raceKey].description : ''}</p>
                {races[raceKey] && (
                  <div className={styles.stats}>
                    <span>❤️ {races[raceKey].health}</span>
                    <span>💪 {races[raceKey].strength}</span>
                    <span>⚡ {races[raceKey].agility}</span>
                  </div>
                )}
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
