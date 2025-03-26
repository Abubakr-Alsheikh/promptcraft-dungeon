// src/types/game.d.ts
export interface Item {
  id: string;
  name: string;
  description: string;
  quantity: number;
  rarity: "common" | "uncommon" | "rare" | "epic" | "legendary";
  icon?: string;
  canUse?: boolean;
  canEquip?: boolean;
  canDrop?: boolean;
}

// You might also add types for player stats, etc.
export interface PlayerStatsData {
  currentHp: number;
  maxHp: number;
  gold: number;
  xp?: number;
  maxXp?: number;
  level?: number;
}

export interface LogEntry {
  id: string | number;
  text: string;
  type: "player" | "system" | "narration" | "error";
  timestamp?: Date;
}

// Add other shared types as needed
