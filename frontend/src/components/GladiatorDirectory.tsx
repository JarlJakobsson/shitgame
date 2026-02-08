import { useEffect, useState } from 'react'
import gameAPI, { PvPGladiatorSummary } from '../services/gameAPI'
import styles from './GladiatorDirectory.module.css'

interface GladiatorDirectoryProps {
  onBack: () => void
  onNotice: (message: string) => void
}

export function GladiatorDirectory({ onBack, onNotice }: GladiatorDirectoryProps) {
  const [gladiators, setGladiators] = useState<PvPGladiatorSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [sendingTo, setSendingTo] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')

  const loadGladiators = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await gameAPI.getPvpGladiators()
      setGladiators(data)
    } catch {
      setError('Failed to load gladiators.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadGladiators()
  }, [])

  const handleChallenge = async (targetPlayerToken: string) => {
    setSendingTo(targetPlayerToken)
    setError('')
    try {
      const response = await gameAPI.sendChallenge(targetPlayerToken)
      setStatus(response.message)
      onNotice(response.message)
    } catch {
      setError('Failed to send challenge.')
    } finally {
      setSendingTo(null)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.panel}>
        <div className={styles.header}>
          <div>
            <div className={styles.title}>Gladiators</div>
            <div className={styles.subtitle}>Challenge other players directly.</div>
          </div>
          <div className={styles.actions}>
            <button className={styles.button} onClick={() => void loadGladiators()} disabled={loading}>
              Refresh
            </button>
            <button className={styles.button} onClick={onBack}>Back</button>
          </div>
        </div>

        {status && <div className={styles.status}>{status}</div>}
        {error && <div className={styles.error}>{error}</div>}

        {gladiators.length === 0 ? (
          <div className={styles.empty}>No other gladiators available right now.</div>
        ) : (
          <div className={styles.list}>
            {gladiators.map((gladiator) => (
              <div key={gladiator.player_token} className={styles.card}>
                <div className={styles.name}>{gladiator.name}</div>
                <div className={styles.line}>Race: {gladiator.race}</div>
                <div className={styles.line}>Level: {gladiator.level}</div>
                <div className={styles.line}>Record: {gladiator.wins}W / {gladiator.losses}L</div>
                <button
                  className={styles.challengeBtn}
                  disabled={sendingTo === gladiator.player_token}
                  onClick={() => void handleChallenge(gladiator.player_token)}
                >
                  {sendingTo === gladiator.player_token ? 'Sending...' : 'Challenge'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
