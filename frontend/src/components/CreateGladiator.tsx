import { useState } from 'react';
import styles from './Arena.module.css';
import humanImg from '../assets/human.png';
import orcImg from '../assets/orc.png';

export function CreateGladiator({ onCreate }: { onCreate: (name: string, race: string) => void }) {
  const [name, setName] = useState('');
  const [race, setRace] = useState<'human' | 'orc' | ''>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name && race) {
      onCreate(name, race);
    }
  };

  return (
    <div className={styles.container}>
      <form className={styles.menu} onSubmit={handleSubmit}>
        <h2>Create Your Gladiator</h2>
        <input
          type="text"
          placeholder="Enter name"
          value={name}
          onChange={e => setName(e.target.value)}
          required
        />
        <div style={{ display: 'flex', gap: 16, margin: '16px 0', justifyContent: 'center' }}>
          <button
            type="button"
            onClick={() => setRace('human')}
            style={{
              border: race === 'human' ? '2px solid gold' : '1px solid #ccc',
              background: '#fff',
              padding: 8,
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: 90,
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            }}
          >
            <img src={humanImg} alt="Human" style={{ width: 48, height: 48, marginBottom: 4 }} />
            <div>Human</div>
          </button>
          <button
            type="button"
            onClick={() => setRace('orc')}
            style={{
              border: race === 'orc' ? '2px solid gold' : '1px solid #ccc',
              background: '#fff',
              padding: 8,
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: 90,
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
            }}
          >
            <img src={orcImg} alt="Orc" style={{ width: 48, height: 48, marginBottom: 4 }} />
            <div>Orc</div>
          </button>
        </div>
        <button className={styles.button} type="submit" disabled={!name || !race}>
          Create Gladiator
        </button>
      </form>
    </div>
  );
}