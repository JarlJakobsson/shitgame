import { useState, useEffect } from 'react';
import gameAPI from '../services/gameAPI';
import styles from './Arena.module.css';
import humanImg from '../assets/human.png';
import orcImg from '../assets/orc.png';

interface ArenaProps {
  onBattleEnd: () => void;
  playerRace: 'human' | 'orc';
}

interface CombatState {
  player_name: string;
  opponent_name: string;
  player_health: number;
  opponent_health: number;
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
        opponent_health: result.opponent.current_health,
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
          <h2>Choose Your Opponent</h2>
          <ul className={styles.enemyList}>
            {Object.entries(enemies).map(([name, data]) => (
              <li key={name} className={styles.enemyItem}>
                <button className={styles.button} onClick={() => handleEnemySelect(name)}>
                  {/* Show image if enemy is orc or human */}
                  {name.toLowerCase() === 'orc' && (
                    <img src={orcImg} alt="Orc" style={{ width: 48, height: 48, marginRight: 8, verticalAlign: 'middle' }} />
                  )}
                  {name.toLowerCase() === 'human' && (
                    <img src={humanImg} alt="Human" style={{ width: 48, height: 48, marginRight: 8, verticalAlign: 'middle' }} />
                  )}
                  <strong>{name}</strong>: {data.description}
                </button>
              </li>
            ))}
          </ul>
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
        <h2>⚔️ ARENA BATTLE ⚔️</h2>
        <div className={styles.fighters}>
          <div className={styles.fighter}>
            {playerRace === 'orc' && (
              <img src={orcImg} alt="Orc" style={{ width: 48, height: 48, marginBottom: 8 }} />
            )}
            {playerRace === 'human' && (
              <img src={humanImg} alt="Human" style={{ width: 48, height: 48, marginBottom: 8 }} />
            )}
            <h3>{combatState.player_name}</h3>
            <div className={styles.healthBar}>
              <div
                className={styles.health}
                style={{ width: `${Math.max(0, (combatState.player_health / 100) * 100)}%` }}
              />
            </div>
            <span>{combatState.player_health} / 100</span>
          </div>

          <div className={styles.vs}>VS</div>

          <div className={styles.fighter}>
            {/* Only show opponent name, not image */}
            <h3>{combatState.opponent_name}</h3>
            <div className={styles.healthBar}>
              <div
                className={styles.health}
                style={{ width: `${Math.max(0, (combatState.opponent_health / 100) * 100)}%` }}
              />
            </div>
            <span>{combatState.opponent_health} / 100</span>
          </div>
        </div>

        <div className={styles.battleLog}>
          <div className={styles.log}>
            {(battleResult && battleResult.battle_log
              ? battleResult.battle_log
              : combatState?.actions || []
            ).map((entry, idx) => (
              <div
                key={idx}
                className={styles.logEntry}
                dangerouslySetInnerHTML={{
                  __html: combatState && typeof entry === 'string'
                    ? entry.replace(new RegExp(combatState.player_name, 'g'), `<strong>${combatState.player_name}</strong>`)
                    : entry
                }}
              />
            ))}
          </div>
        </div>

        {battleEnded && battleResult && (
          <div className={styles.result}>
            <h3>{battleResult.result === 'victory' ? '🏆 VICTORY! 🏆' : '💀 DEFEAT 💀'}</h3>
            <p>Gold: {battleResult.gladiator.gold}</p>
            <p>Experience: {battleResult.gladiator.experience}</p>
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
  );
}
