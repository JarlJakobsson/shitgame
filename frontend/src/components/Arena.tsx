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

const getOpponentImage = (opponentName: string, opponentRace?: string): string | undefined => {
  const opponentNameKey = opponentName.toLowerCase();
  if (enemyImages[opponentNameKey]) {
    return enemyImages[opponentNameKey];
  }

  if (!opponentRace) {
    return undefined;
  }

  return enemyImages[opponentRace.toLowerCase()];
};

interface ArenaProps {
  onBattleEnd: () => void;
  playerRace: string;
  replayData?: ArenaReplayData | null;
}

interface ArenaReplayData {
  player_name: string;
  player_race: string;
  opponent_name: string;
  opponent_race: string;
  player_health: number;
  player_max_health: number;
  opponent_health: number;
  opponent_max_health: number;
  rounds: number;
  result: 'victory' | 'defeat';
  reward_gold: number;
  reward_exp: number;
  battle_log: string[];
}

interface CombatState {
  player_name: string;
  opponent_name: string;
  opponent_race?: string;
  player_health: number;
  player_max_health: number;
  opponent_health: number;
  opponent_max_health: number;
  round: number;
  actions: string[];
}

const buildReplayState = (replay: ArenaReplayData): CombatState => ({
  player_name: replay.player_name,
  opponent_name: replay.opponent_name,
  opponent_race: replay.opponent_race,
  player_health: replay.player_health,
  player_max_health: replay.player_max_health,
  opponent_health: replay.opponent_health,
  opponent_max_health: replay.opponent_max_health,
  round: replay.rounds,
  actions: replay.battle_log,
});

const buildReplayResult = (replay: ArenaReplayData) => ({
  result: replay.result,
  gladiator: null,
  reward_gold: replay.reward_gold,
  reward_exp: replay.reward_exp,
  battle_log: replay.battle_log,
});

export function Arena({ onBattleEnd, playerRace, replayData = null }: ArenaProps) {
  const [combatState, setCombatState] = useState<CombatState | null>(
    replayData ? buildReplayState(replayData) : null
  );
  const [loading, setLoading] = useState(false);
  const [battleEnded, setBattleEnded] = useState(Boolean(replayData));
  const [battleResult, setBattleResult] = useState<{ result: string; gladiator: any; reward_gold: number; reward_exp: number; battle_log: string[] } | null>(
    replayData ? buildReplayResult(replayData) : null
  );
  const [enemyMenuOpen, setEnemyMenuOpen] = useState(!replayData);
  const [enemies, setEnemies] = useState<Record<string, any>>({});
  const [arenaError, setArenaError] = useState('');

  useEffect(() => {
    if (replayData) {
      setCombatState(buildReplayState(replayData));
      setBattleResult(buildReplayResult(replayData));
      setBattleEnded(true);
      setEnemyMenuOpen(false);
      return;
    }
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
  }, [replayData]);

  const handleEnemySelect = async (enemyName: string) => {
    setEnemyMenuOpen(false);
    setLoading(true);
    setArenaError('');
    try {
      const result = await gameAPI.startCombatWithEnemy(enemyName);
      const initialState = {
        player_name: result.player.name,
        opponent_name: result.opponent.name,
        opponent_race: result.opponent.race,
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
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setArenaError(typeof detail === 'string' ? detail : 'Failed to start combat.');
      setEnemyMenuOpen(true);
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
  if (enemyMenuOpen && !replayData) {
    return (
      <div className={styles.container}>
        <div className={styles.menu}>
          <div className={styles.menuHeader}>
            <h2>Choose Your Opponent</h2>
            <p>Pick your next challenge and earn your glory.</p>
            {arenaError && <p className={styles.menuError}>{arenaError}</p>}
            <div className={styles.menuActions}>
              <button className={styles.button} onClick={onBattleEnd}>
                Back
              </button>
            </div>
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

  const opponentImage = getOpponentImage(combatState.opponent_name, combatState.opponent_race);

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
            {opponentImage && (
              <img
                src={opponentImage}
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
