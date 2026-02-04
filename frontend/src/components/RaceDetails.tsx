import { Race } from '../services/gameAPI';
import styles from './RaceDetails.module.css';
import humanImg from '../assets/human.png';
import orcImg from '../assets/orc.png';
import goblinImg from '../assets/goblin.png';
import minotaurImg from '../assets/minotaur.png';
import skeletonImg from '../assets/skeleton.png';

interface RaceDetailsProps {
  raceName: string;
  race: Race;
  onConfirm: () => void;
  onBack: () => void;
}

const raceImages: Record<string, string> = {
  human: humanImg,
  orc: orcImg,
  goblin: goblinImg,
  minotaur: minotaurImg,
  skeleton: skeletonImg,
};

export function RaceDetails({ raceName, race, onConfirm, onBack }: RaceDetailsProps) {
  const raceKey = raceName.toLowerCase();
  const raceImage = raceImages[raceKey];

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h2>{raceName}</h2>
          <p className={styles.subtitle}>Know your strengths before entering the arena.</p>
        </div>

        {raceImage && (
          <img className={styles.image} src={raceImage} alt={raceName} />
        )}

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

        <div className={styles.stats}>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Health</span>
            <span className={styles.statValue}>{race.health}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Strength</span>
            <span className={styles.statValue}>{race.strength}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Agility</span>
            <span className={styles.statValue}>{race.agility}</span>
          </div>
        </div>

        <div className={styles.actions}>
          <button className={styles.secondaryButton} type="button" onClick={onBack}>
            Go Back
          </button>
          <button className={styles.primaryButton} type="button" onClick={onConfirm}>
            Confirm Race
          </button>
        </div>
      </div>
    </div>
  );
}
