import styles from './MainMenu.module.css';

interface MainMenuProps {
  onCreateGladiator: () => void;
  onQuit: () => void;
}

export function MainMenu({ onCreateGladiator, onQuit }: MainMenuProps) {
  return (
    <div className={styles.container}>
      <div className={styles.menu}>
        <h1>⚔️ GLADIATOR ARENA ⚔️</h1>
        <button className={styles.button} onClick={onCreateGladiator}>
          Create Gladiator
        </button>
        <button className={styles.button} onClick={onQuit}>
          Quit
        </button>
      </div>
    </div>
  );
}
