import { useState, useEffect } from 'react';
import gameAPI, { Gladiator, Race } from './services/gameAPI';
import { MainMenu } from './components/MainMenu';
import { RaceSelection } from './components/RaceSelection';
import { RaceDetails } from './components/RaceDetails';
import { GladiatorCreation } from './components/GladiatorCreation';
import { GameDashboard } from './components/GameDashboard';
import { Arena } from './components/Arena';
import './App.css';

type GameState = 'menu' | 'race-selection' | 'race-details' | 'gladiator-creation' | 'dashboard' | 'arena';

function App() {
  const [gameState, setGameState] = useState<GameState>('menu');
  const [selectedRace, setSelectedRace] = useState<string | null>(null);
  const [gladiator, setGladiator] = useState<Gladiator | null>(null);
  const [races, setRaces] = useState<Record<string, Race>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadRaces();
  }, []);

  const loadRaces = async () => {
    try {
      const racesData = await gameAPI.getRaces();
      setRaces(racesData);
    } catch (err) {
      console.error('Failed to load races:', err);
    }
  };

  const handleCreateGladiator = () => {
    setGameState('race-selection');
  };

  const handleRaceSelected = (race: string) => {
    setSelectedRace(race);
    setGameState('race-details');
  };

  const handleRaceBack = () => {
    setGameState('race-selection');
  };

  const handleRaceConfirm = () => {
    if (selectedRace) {
      setGameState('gladiator-creation');
    }
  };

  const handleGladiatorCreated = async () => {
    const gladiatorData = await gameAPI.getGladiator();
    setGladiator(gladiatorData);
    setGameState('dashboard');
  };

  const handleTrain = async () => {
    setLoading(true);
    try {
      const updated = await gameAPI.trainGladiator();
      setGladiator(updated);
    } catch (err) {
      console.error('Failed to train:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFight = () => {
    setGameState('arena');
  };

  const handleBattleEnd = async () => {
    const updated = await gameAPI.getGladiator();
    setGladiator(updated);
    setGameState('dashboard');
  };

  const handleLogout = () => {
    setGameState('menu');
    setGladiator(null);
    setSelectedRace(null);
  };

  return (
    <div className="app">
      {gameState === 'menu' && (
        <MainMenu
          onCreateGladiator={handleCreateGladiator}
          onQuit={() => {}}
        />
      )}

      {gameState === 'race-selection' && (
        <RaceSelection races={races} onSelectRace={handleRaceSelected} />
      )}

      {gameState === 'race-details' && selectedRace && races[selectedRace] && (
        <RaceDetails
          raceName={selectedRace}
          race={races[selectedRace]}
          onBack={handleRaceBack}
          onConfirm={handleRaceConfirm}
        />
      )}

      {gameState === 'gladiator-creation' && selectedRace && (
        <GladiatorCreation
          raceName={selectedRace}
          onGladiatorCreated={handleGladiatorCreated}
        />
      )}

      {gameState === 'dashboard' && gladiator && (
        <GameDashboard
          gladiator={gladiator}
          onTrain={handleTrain}
          onFight={handleFight}
          onLogout={handleLogout}
          loading={loading}
        />
      )}

      {gameState === 'arena' && gladiator && (
        <Arena
          onBattleEnd={handleBattleEnd}
          playerRace={
            gladiator.race && typeof gladiator.race === 'string'
              ? gladiator.race.toLowerCase()
              : 'human'
          }
        />
      )}
    </div>
  );
}

export default App;
