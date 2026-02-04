import { Race } from '../services/gameAPI';
import styles from './RaceSelection.module.css';
import humanImg from '../assets/human.png';
import orcImg from '../assets/orc.png';
import goblinImg from '../assets/goblin.png';
import minotaurImg from '../assets/minotaur.png';
import skeletonImg from '../assets/skeleton.png';

interface RaceSelectionProps {
  races: Record<string, Race>;
  onSelectRace: (raceName: string) => void;
}

const raceImages: Record<string, string> = {
  human: humanImg,
  orc: orcImg,
  goblin: goblinImg,
  minotaur: minotaurImg,
  skeleton: skeletonImg,
};

export function RaceSelection({ races, onSelectRace }: RaceSelectionProps) {
  // Keep original keys for API compatibility, and render all races returned by the API.
  const raceKeys = Object.keys(races);

  if (raceKeys.length === 0) {
    return <div className={styles.container}><div>Loading races...</div></div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h2>Select Your Race</h2>
        <div className={styles.raceList}>
          {raceKeys.map(raceKey => {
            const raceKeyLower = raceKey.toLowerCase();
            return (
            <div
              key={raceKey}
              className={styles.raceOption}
              onClick={() => onSelectRace(raceKey)}
            >
              <img
                src={raceImages[raceKeyLower]}
                alt={raceKey}
                className={styles.raceImage}
              />
              <div className={styles.raceDetails}>
                <h3>{raceKey}</h3>
                {races[raceKey] && (
                  <div className={styles.stats}>
                    <span>{'\u2764\uFE0F'} {races[raceKey].health}</span>
                    <span>{'\uD83D\uDCAA'} {races[raceKey].strength}</span>
                    <span>{'\u26A1'} {races[raceKey].agility}</span>
                  </div>
                )}
              </div>
            </div>
          )})}
        </div>
      </div>
    </div>
  );
}
