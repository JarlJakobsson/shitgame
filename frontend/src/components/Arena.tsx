import { useState, useEffect } from 'react';
import gameAPI from '../services/gameAPI';
import styles from './Arena.module.css';
import humanImg from '../assets/human.png';
import orcImg from '../assets/orc.png';
import banditImg from '../assets/bandit.png';
import darkKnightImg from '../assets/darkknight.png';
import goblinImg from '../assets/goblin.png';
import minotaurImg from '../assets/minotaur.png';
import skeletonImg from '../assets/skeleton.png';
import slimeImg from '../assets/slime.png';

const enemyImages: Record<string, string> = {
  human: humanImg,
  orc: orcImg,
  bandit: banditImg,
  'dark knight': darkKnightImg,
  goblin: goblinImg,
  minotaur: minotaurImg,
  skeleton: skeletonImg,
  slime: slimeImg,
};

interface ArenaProps {
  onBattleEnd: () => void;
  playerRace: string;
}

interface CombatState {
  player_name: string;
  opponent_name: string;
  player_health: number;
  player_max_health: number;
  opponent_health: number;
  opponent_max_health: number;
  round: number;
  actions: string[];
}

export function Arena({ onBattleEnd, playerRace }: ArenaProps) {
  const [combatState, setCombatState] = useState<CombatState | null>(null);
  const [loading, setLoading] = useState(false);
  const [battleEnded, setBattleEnded] = useState(false);
  const [battleResult, setBattleResult] = useState<{ result: string; gladiator: any; reward_gold: number; reward_exp: number; battle_log: string[] } | null>(null);
  const [enemyMenuOpen, setEnemyMenuOpen] = useState(true);
  const [enemies, setEnemies] = useState<Record<string, any>>({});

  useEffect(() => {
    // Fetch enemy list on mount
    const fetchEnemies = async () => {
      try {
        const data = await gameAPI.getEnemies();
        setEnemies(data);
      } catch (err) {
        setEnemies({});
      }
    };
    fetchEnemies();
  }, []);

  const handleEnemySelect = async (enemyName: string) => {
    setEnemyMenuOpen(false);
    setLoading(true);
    try {
      const result = await gameAPI.startCombatWithEnemy(enemyName);
      const initialState = {
        player_name: result.player.name,
        opponent_name: result.opponent.name,
        player_health: result.player.current_health,
        player_max_health: result.player.max_health,
        opponent_health: result.opponent.current_health,
        opponent_max_health: result.opponent.max_health,
        round: 0,
        actions: [],
      };
      setCombatState(initialState);
      setLoading(false);
      simulateAllRounds(initialState);
    } catch (err) {
      setLoading(false);
    }
  };

  const simulateAllRounds = async (initialState: CombatState) => {
    let currentState = initialState;
    let roundEnded = false;

    while (!roundEnded) {
      try {
        const roundResult = await gameAPI.executeCombatRound();
        
        currentState = {
          ...currentState,
          round: roundResult.round,
          player_health: roundResult.player_health,
          opponent_health: roundResult.opponent_health,
          actions: [...currentState.actions, ...roundResult.actions],
        };
        
        setCombatState(currentState);

        if (roundResult.winner) {
          roundEnded = true;
          setBattleEnded(true);
          const result = await gameAPI.finishCombat();
          setBattleResult(result);
        }
      } catch (err) {
        console.error('Failed to execute round:', err);
        roundEnded = true;
      }
    }
  };

  if (loading && !combatState) {
    return <div className={styles.container}><div>Loading arena...</div></div>;
  }

  // Show enemy selection menu if not in combat
  if (enemyMenuOpen) {
    return (
      <div className={styles.container}>
        <div className={styles.menu}>
          <div className={styles.menuHeader}>
            <h2>Choose Your Opponent</h2>
            <p>Pick your next challenge and earn your glory.</p>
          </div>
          <div className={styles.enemyGrid}>
            {Object.entries(enemies).map(([name, data]) => {
              const imageKey = name.toLowerCase();
              const enemyImage = enemyImages[imageKey];
              return (
                <button
                  key={name}
                  className={styles.enemyCard}
                  onClick={() => handleEnemySelect(name)}
                >
                  <div className={styles.enemyPortrait}>
                    {enemyImage && (
                      <img src={enemyImage} alt={name} className={styles.enemyImage} />
                    )}
                  </div>
                  <div className={styles.enemyInfo}>
                    <div className={styles.enemyName}>{name}</div>
                    {typeof data.min_level === 'number' && (
                      <div className={styles.enemyLevel}>
                        Level {data.min_level}+
                      </div>
                    )}
                    <div className={styles.enemyDesc}>{data.description}</div>
                  </div>
                  <div className={styles.enemyAction}>Fight</div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  if (!combatState) {
    return <div className={styles.container}><div>Failed to load arena</div></div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.arena}>
        <div className={styles.arenaHeader}>
          <h2> BATTLE </h2>
        </div>

        <div className={styles.arenaGrid}>
          <div className={styles.fighter}>
            {enemyImages[playerRace.toLowerCase()] && (
              <img
                src={enemyImages[playerRace.toLowerCase()]}
                alt={playerRace}
                className={styles.fighterImage}
              />
            )}
            <h3>{combatState.player_name}</h3>
            <div className={styles.healthBar}>
              <div
                className={styles.health}
                style={{ width: `${Math.max(0, (combatState.player_health / Math.max(1, combatState.player_max_health)) * 100)}%` }}
              />
            </div>
            <span>{combatState.player_health} / {combatState.player_max_health}</span>
          </div>

          <div className={styles.centerColumn}>
            <div className={styles.centerCard}>
              <div className={styles.vsBadge}>VS</div>

              <div className={styles.battleLog}>
                <div className={styles.log}>
                {(battleResult && battleResult.battle_log
                  ? battleResult.battle_log
                  : combatState?.actions || []
                ).map((entry, idx) => {
                  const isRoundMarker = typeof entry === 'string' && entry.startsWith('Round ');
                  const entryClassName = isRoundMarker
                    ? `${styles.logEntry} ${styles.roundMarker}`
                    : styles.logEntry;

                  if (typeof entry !== 'string') {
                    return (
                      <div key={idx} className={entryClassName}>
                        {String(entry)}
                      </div>
                    );
                  }

                  if (!combatState?.player_name) {
                    return (
                      <div key={idx} className={entryClassName}>
                        {entry}
                      </div>
                    );
                  }

                  const name = combatState.player_name;
                  const segments = entry.split(name);

                  return (
                    <div key={idx} className={entryClassName}>
                      <span>
                        {segments.map((segment, segmentIndex) => (
                          <span key={segmentIndex}>
                            {segment}
                            {segmentIndex < segments.length - 1 && <strong>{name}</strong>}
                          </span>
                        ))}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

              {battleEnded && battleResult && (
                <div className={styles.result}>
                  <h3>
                    {battleResult.result === 'victory'
                      ? `${'\uD83C\uDFC6'} VICTORY! ${'\uD83C\uDFC6'}`
                      : `${'\uD83D\uDC80'} DEFEAT ${'\uD83D\uDC80'}`}
                  </h3>
                  <p>Gold gained: +{battleResult.reward_gold}</p>
                  <p>Experience gained: +{battleResult.reward_exp}</p>
                </div>
              )}

              <div className={styles.actions}>
                {battleEnded ? (
                  <button
                    className={styles.button}
                    onClick={onBattleEnd}
                  >
                    Return to Dashboard
                  </button>
                ) : (
                  <div>Simulating battle...</div>
                )}
              </div>
            </div>
          </div>

          <div className={styles.fighter}>
            {enemyImages[combatState.opponent_name.toLowerCase()] && (
              <img
                src={enemyImages[combatState.opponent_name.toLowerCase()]}
                alt={combatState.opponent_name}
                className={styles.fighterImage}
              />
            )}
            <h3>{combatState.opponent_name}</h3>
            <div className={styles.healthBar}>
              <div
                className={styles.health}
                style={{ width: `${Math.max(0, (combatState.opponent_health / Math.max(1, combatState.opponent_max_health)) * 100)}%` }}
              />
            </div>
            <span>{combatState.opponent_health} / {combatState.opponent_max_health}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
