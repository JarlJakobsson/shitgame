import { useState } from 'react';
import gameAPI, { StatPlan } from '../services/gameAPI';
import styles from './GladiatorCreation.module.css';

interface GladiatorCreationProps {
  raceName: string;
  stats: StatPlan;
  onGladiatorCreated: () => void;
}

export function GladiatorCreation({ raceName, stats, onGladiatorCreated }: GladiatorCreationProps) {
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Please enter a name');
      return;
    }

    setLoading(true);
    try {
      await gameAPI.createGladiator(name, raceName, stats);
      onGladiatorCreated();
    } catch (err) {
      setError('Failed to create gladiator');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h2>Create Your Gladiator</h2>
        <p className={styles.raceInfo}>Race: <strong>{raceName}</strong></p>
        
        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label htmlFor="name">Gladiator Name:</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError('');
              }}
              placeholder="Enter your gladiator's name"
              disabled={loading}
            />
          </div>

          {error && <p className={styles.error}>{error}</p>}

          <button type="submit" className={styles.button} disabled={loading}>
            {loading ? 'Creating...' : 'Create Gladiator'}
          </button>
        </form>
      </div>
    </div>
  );
}
