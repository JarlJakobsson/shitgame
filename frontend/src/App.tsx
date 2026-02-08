import { useEffect, useMemo, useState } from 'react'
import './App.css'
import gameAPI, { GladiatorWithEquipment, Race, StatPlan } from './services/gameAPI'
import { MainMenu } from './components/MainMenu'
import { RaceSelection } from './components/RaceSelection'
import { RaceDetails } from './components/RaceDetails'
import { GladiatorCreation } from './components/GladiatorCreation'
import { GameDashboard } from './components/GameDashboard'
import { Arena } from './components/Arena'
import { LevelUpPlanner } from './components/LevelUpPlanner'

type View =
  | 'menu'
  | 'raceSelection'
  | 'raceDetails'
  | 'gladiatorCreation'
  | 'dashboard'
  | 'arena'
  | 'levelUp'

const DEFAULT_STATS: StatPlan = {
  strength: 0,
  health: 0,
  stamina: 0,
  dodge: 0,
  initiative: 0,
  weaponskill: 0,
}

export default function App() {
  const [view, setView] = useState<View>('menu')
  const [races, setRaces] = useState<Record<string, Race>>({})
  const [selectedRaceName, setSelectedRaceName] = useState<string | null>(null)
  const [selectedStats, setSelectedStats] = useState<StatPlan>(DEFAULT_STATS)
  const [gladiator, setGladiator] = useState<GladiatorWithEquipment | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [queuedForRandomBattle, setQueuedForRandomBattle] = useState(false)
  const [notices, setNotices] = useState<string[]>([])

  useEffect(() => {
    void loadRaces()
  }, [])

  useEffect(() => {
    if (!gladiator) {
      setQueuedForRandomBattle(false)
      return
    }

    let active = true
    const pollNotifications = async () => {
      try {
        const data = await gameAPI.getNotifications()
        if (!active) {
          return
        }
        setQueuedForRandomBattle(data.queued_for_random_battle)
        if (data.notifications.length > 0) {
          const messages = data.notifications.map((item) => item.message)
          setNotices((prev) => [...messages, ...prev].slice(0, 8))
          const refreshed = await gameAPI.getGladiatorWithEquipment()
          if (!active) {
            return
          }
          setGladiator(refreshed)
        }
      } catch {
        // Ignore transient poll failures.
      }
    }

    void pollNotifications()
    const intervalId = window.setInterval(() => {
      void pollNotifications()
    }, 2500)

    return () => {
      active = false
      window.clearInterval(intervalId)
    }
  }, [gladiator?.name])

  const loadRaces = async () => {
    try {
      const data = await gameAPI.getRaces()
      setRaces(data)
    } catch (err) {
      setError('Failed to load races.')
    }
  }

  const selectedRace = useMemo(() => {
    if (!selectedRaceName) {
      return null
    }
    return races[selectedRaceName] || null
  }, [races, selectedRaceName])

  const handleCreateGladiator = () => {
    setError('')
    setView('raceSelection')
  }

  const handleSelectRace = (raceName: string) => {
    setSelectedRaceName(raceName)
    setSelectedStats(DEFAULT_STATS)
    setError('')
    setView('raceDetails')
  }

  const handleConfirmRace = (stats: StatPlan) => {
    setSelectedStats(stats)
    setError('')
    setView('gladiatorCreation')
  }

  const handleGladiatorCreated = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await gameAPI.getGladiatorWithEquipment()
      setGladiator(data)
      setView('dashboard')
    } catch (err) {
      setError('Failed to load gladiator.')
    } finally {
      setLoading(false)
    }
  }

  const handleTrain = async () => {
    setLoading(true)
    setError('')
    try {
      await gameAPI.trainGladiator()
      const data = await gameAPI.getGladiatorWithEquipment()
      setGladiator(data)
    } catch (err) {
      setError('Failed to train gladiator.')
    } finally {
      setLoading(false)
    }
  }

  const handleFight = () => {
    setError('')
    setView('arena')
  }

  const handleBattleEnd = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await gameAPI.getGladiatorWithEquipment()
      setGladiator(data)
    } catch (err) {
      setError('Failed to refresh gladiator after battle.')
    } finally {
      setLoading(false)
      setView('dashboard')
    }
  }

  const handleLogout = () => {
    setGladiator(null)
    setSelectedRaceName(null)
    setSelectedStats(DEFAULT_STATS)
    setQueuedForRandomBattle(false)
    setNotices([])
    setError('')
    setView('menu')
  }

  const handleQuit = () => {
    handleLogout()
  }

  const handleAllocateStats = () => {
    if (gladiator && gladiator.stat_points > 0) {
      setError('')
      setView('levelUp')
    }
  }

  const handleConfirmAllocateStats = async (stats: StatPlan) => {
    setLoading(true)
    setError('')
    try {
      await gameAPI.allocateStats(stats)
      const data = await gameAPI.getGladiatorWithEquipment()
      setGladiator(data)
      setView('dashboard')
    } catch (err) {
      setError('Failed to allocate stats.')
    } finally {
      setLoading(false)
    }
  }

  const handleRandomBattle = async () => {
    setLoading(true)
    setError('')
    try {
      const result = await gameAPI.joinRandomBattle()
      if (result.status === 'queued') {
        setQueuedForRandomBattle(true)
      }
      setNotices((prev) => [result.message, ...prev].slice(0, 8))
    } catch {
      setError('Failed to enter random battle queue.')
    } finally {
      setLoading(false)
    }
  }

  let content = (
    <MainMenu onCreateGladiator={handleCreateGladiator} onQuit={handleQuit} />
  )

  if (view === 'raceSelection') {
    content = <RaceSelection races={races} onSelectRace={handleSelectRace} />
  } else if (view === 'raceDetails') {
    if (selectedRaceName && selectedRace) {
      content = (
        <RaceDetails
          raceName={selectedRaceName}
          race={selectedRace}
          initialStats={selectedStats}
          onConfirm={handleConfirmRace}
          onBack={() => setView('raceSelection')}
        />
      )
    } else {
      content = <RaceSelection races={races} onSelectRace={handleSelectRace} />
    }
  } else if (view === 'gladiatorCreation') {
    if (selectedRaceName) {
      content = (
        <GladiatorCreation
          raceName={selectedRaceName}
          stats={selectedStats}
          onGladiatorCreated={handleGladiatorCreated}
        />
      )
    } else {
      content = <RaceSelection races={races} onSelectRace={handleSelectRace} />
    }
  } else if (view === 'dashboard') {
    if (gladiator) {
      content = (
        <GameDashboard
          gladiator={gladiator}
          onTrain={handleTrain}
          onFight={handleFight}
          onRandomBattle={handleRandomBattle}
          onAllocateStats={handleAllocateStats}
          onLogout={handleLogout}
          loading={loading}
          queuedForRandomBattle={queuedForRandomBattle}
          onGladiatorUpdate={setGladiator}
        />
      )
    } else {
      content = (
        <MainMenu
          onCreateGladiator={handleCreateGladiator}
          onQuit={handleQuit}
        />
      )
    }
  } else if (view === 'arena') {
    if (gladiator) {
      content = (
        <Arena onBattleEnd={handleBattleEnd} playerRace={gladiator.race} />
      )
    } else {
      content = (
        <MainMenu
          onCreateGladiator={handleCreateGladiator}
          onQuit={handleQuit}
        />
      )
    }
  } else if (view === 'levelUp') {
    if (gladiator) {
      content = (
        <LevelUpPlanner
          pointsAvailable={gladiator.stat_points}
          onConfirm={handleConfirmAllocateStats}
          onCancel={() => setView('dashboard')}
        />
      )
    } else {
      content = (
        <MainMenu
          onCreateGladiator={handleCreateGladiator}
          onQuit={handleQuit}
        />
      )
    }
  }

  return (
    <div className="app">
      {error && <div className="app__error">{error}</div>}
      {notices.length > 0 && (
        <div className="app__error">
          {notices[0]}
        </div>
      )}
      {content}
    </div>
  )
}
