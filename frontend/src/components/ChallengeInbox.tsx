import { useEffect, useState } from 'react'
import gameAPI, { IncomingChallenge } from '../services/gameAPI'
import styles from './ChallengeInbox.module.css'

interface ChallengeInboxProps {
  onBack: () => void
  onNotice: (message: string) => void
}

export function ChallengeInbox({ onBack, onNotice }: ChallengeInboxProps) {
  const [challenges, setChallenges] = useState<IncomingChallenge[]>([])
  const [loading, setLoading] = useState(false)
  const [processingId, setProcessingId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')

  const loadChallenges = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await gameAPI.getIncomingChallenges()
      setChallenges(data.challenges)
    } catch {
      setError('Failed to load challenges.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadChallenges()
  }, [])

  const handleAccept = async (challengeId: number) => {
    setProcessingId(challengeId)
    setError('')
    try {
      const response = await gameAPI.acceptChallenge(challengeId)
      const winner = response.battle_result?.winner_name
      const loser = response.battle_result?.loser_name
      const rounds = response.battle_result?.rounds
      const message = winner && loser && rounds
        ? `Challenge accepted: ${winner} defeated ${loser} in ${rounds} rounds.`
        : response.message
      setStatus(message)
      onNotice(message)
      await loadChallenges()
    } catch {
      setError('Failed to accept challenge.')
    } finally {
      setProcessingId(null)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.panel}>
        <div className={styles.header}>
          <div>
            <div className={styles.title}>Challenges</div>
            <div className={styles.subtitle}>Incoming challenge requests from other gladiators.</div>
          </div>
          <div className={styles.actions}>
            <button className={styles.button} onClick={() => void loadChallenges()} disabled={loading}>
              Refresh
            </button>
            <button className={styles.button} onClick={onBack}>Back</button>
          </div>
        </div>

        {status && <div className={styles.status}>{status}</div>}
        {error && <div className={styles.error}>{error}</div>}

        {challenges.length === 0 ? (
          <div className={styles.empty}>No active challenges right now.</div>
        ) : (
          <div className={styles.list}>
            {challenges.map((challenge) => (
              <div key={challenge.id} className={styles.row}>
                <div className={styles.name}>{challenge.challenger_name}</div>
                <div className={styles.line}>Race: {challenge.challenger_race}</div>
                <div className={styles.line}>Level: {challenge.challenger_level}</div>
                {challenge.created_at && (
                  <div className={styles.line}>
                    Sent: {new Date(challenge.created_at).toLocaleString()}
                  </div>
                )}
                <button
                  className={styles.acceptBtn}
                  disabled={processingId === challenge.id}
                  onClick={() => void handleAccept(challenge.id)}
                >
                  {processingId === challenge.id ? 'Accepting...' : 'Accept Challenge'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
