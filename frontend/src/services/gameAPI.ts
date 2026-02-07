
import axios from 'axios';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? 'http://localhost:5000' : '/api');

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
  stat_points: number;
  vitality: number;
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
  pros?: string[];
  cons?: string[];
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

export interface EnemySummary {
  health: number;
  strength: number;
  dodge: number;
  initiative: number;
  weaponskill: number;
  stamina: number;
  min_level?: number;
  description?: string;
}

export interface Combatant {
  name: string;
  race?: string;
  current_health: number;
  max_health: number;
  strength: number;
  dodge: number;
  initiative: number;
  weaponskill: number;
  stamina: number;
}

export interface CombatStartResponse {
  player: Gladiator;
  opponent: Combatant;
  message: string;
}

export interface CombatRoundResponse {
  round: number;
  actions: string[];
  player_health: number;
  opponent_health: number;
  winner?: string;
}

export interface CombatFinishResponse {
  result: 'victory' | 'defeat';
  gladiator: Gladiator;
  reward_gold: number;
  reward_exp: number;
  battle_log: string[];
}

export interface Equipment {
  id: number;
  name: string;
  slot: string;
  item_type: string;
  rarity: string;
  level_requirement: number;
  strength_bonus: number;
  vitality_bonus: number;
  stamina_bonus: number;
  dodge_bonus: number;
  initiative_bonus: number;
  weaponskill_bonus: number;
  value: number;
  description?: string;
}

export interface GladiatorEquipment {
  id: number;
  equipment: Equipment;
  is_equipped: boolean;
}

export interface EquipmentSlotRequest {
  equipment_id: number;
  slot: string;
}

export interface ShopInventory {
  available_items: Equipment[];
}

export interface GladiatorWithEquipment extends Gladiator {
  equipped_items?: Record<string, Equipment>;
  inventory?: GladiatorEquipment[];
}

export const gameAPI = {
  getEnemies: async (): Promise<Record<string, EnemySummary>> => {
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

  startCombat: async (): Promise<CombatStartResponse> => {
    const response = await api.post('/combat/start');
    return response.data;
  },

  startCombatWithEnemy: async (enemyName: string): Promise<CombatStartResponse> => {
    const response = await api.post('/combat/start', { enemy_name: enemyName });
    return response.data;
  },

  executeCombatRound: async (): Promise<CombatRoundResponse> => {
    const response = await api.post('/combat/round');
    return response.data;
  },

  finishCombat: async (): Promise<CombatFinishResponse> => {
    const response = await api.post('/combat/finish');
    return response.data;
  },

  allocateStats: async (stats: StatPlan): Promise<Gladiator> => {
    const response = await api.post('/gladiator/allocate', stats);
    return response.data;
  },

  getAllEquipment: async (): Promise<Equipment[]> => {
    const response = await api.get('/equipment');
    return response.data;
  },

  getShopInventory: async (): Promise<ShopInventory> => {
    const response = await api.get('/equipment/shop');
    return response.data;
  },

  getGladiatorEquipment: async (): Promise<GladiatorEquipment[]> => {
    const response = await api.get('/gladiator/equipment');
    return response.data;
  },

  getEquippedItems: async (): Promise<Record<string, Equipment>> => {
    const response = await api.get('/gladiator/equipment/equipped');
    return response.data;
  },

  equipItem: async (request: EquipmentSlotRequest): Promise<{ message: string }> => {
    const response = await api.post('/equipment/equip', request);
    return response.data;
  },

  unequipItem: async (slot: string): Promise<{ message: string }> => {
    const response = await api.post('/equipment/unequip', null, {
      params: { slot }
    });
    return response.data;
  },

  purchaseEquipment: async (equipmentId: number): Promise<Gladiator> => {
    const response = await api.post(`/equipment/purchase/${equipmentId}`);
    return response.data;
  },

  getGladiatorWithEquipment: async (): Promise<GladiatorWithEquipment> => {
    const response = await api.get('/gladiator');
    return response.data;
  },
};

export default gameAPI;
