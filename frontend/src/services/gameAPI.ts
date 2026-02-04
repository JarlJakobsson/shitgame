
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export interface Gladiator {
  weaponskill: number;
  initiative: number;
  name: string;
  race: string;
  level: number;
  experience: number;
  current_health: number;
  max_health: number;
  strength: number;
  dodge: number;
  gold: number;
  wins: number;
  losses: number;
  stamina: number;
}

export interface Race {
  weaponskill: number;
  initiative: number;
  health: number;
  strength: number;
  dodge: number;
  description: string;
  origin?: string;
  specialty?: string;
  racials?: { title: string; description: string }[];
  racial_bonus?: { stat: string; value: string }[];
}

export interface StatPlan {
  strength: number;
  health: number;
  stamina: number;
  dodge: number;
  initiative: number;
  weaponskill: number;
}

export const gameAPI = {
  getEnemies: async (): Promise<Record<string, any>> => {
    const response = await api.get('/enemies');
    return response.data;
  },
  getRaces: async (): Promise<Record<string, Race>> => {
    const response = await api.get('/races');
    return response.data;
  },

  createGladiator: async (name: string, race: string, stats: StatPlan): Promise<Gladiator> => {
    const response = await api.post('/gladiator', { name, race, ...stats });
    return response.data;
  },

  getGladiator: async (): Promise<Gladiator> => {
    const response = await api.get('/gladiator');
    return response.data;
  },

  trainGladiator: async (): Promise<Gladiator> => {
    const response = await api.post('/gladiator/train');
    return response.data;
  },

  startCombat: async () => {
    const response = await api.post('/combat/start');
    return response.data;
  },

  startCombatWithEnemy: async (enemyName: string) => {
    const response = await api.post('/combat/start', { enemy_name: enemyName });
    return response.data;
  },

  executeCombatRound: async () => {
    const response = await api.post('/combat/round');
    return response.data;
  },

  finishCombat: async () => {
    const response = await api.post('/combat/finish');
    return response.data;
  },
};

export default gameAPI;
