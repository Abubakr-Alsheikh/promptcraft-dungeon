import { PlayerStatsData, Item, LogEntry } from "@/types/game";

// --- Slice Interfaces (Define the shape of each part) ---

export interface GameStateSliceState {
  gameId: number | null;
  playerStats: PlayerStatsData | null;
  inventory: Item[];
  description: string;
  logs: LogEntry[];
  isStartingGame: boolean;
  isProcessingCommand: boolean;
}

export interface GameStateSliceActions {
  startGame: (playerName: string, difficulty: string) => Promise<boolean>;
  sendCommand: (command: string) => Promise<void>;
  _addLog: (log: Omit<LogEntry, "id" | "timestamp">) => void;
  resetGameState: () => void;
}

export type ItemSliceState = unknown;

export interface ItemSliceActions {
  useItem: (itemId: string) => Promise<void>;
  equipItem: (itemId: string) => Promise<void>;
  dropItem: (itemId: string) => Promise<void>;
}

export interface UISliceState {
  isInventoryOpen: boolean;
  isSettingsOpen: boolean;
}

export interface UISliceActions {
  toggleInventory: (open?: boolean) => void;
  toggleSettings: (open?: boolean) => void;
}

export interface SettingsSliceState {
  animationSpeed: number;
  masterVolume: number;
  effectsVolume: number;
}

export interface SettingsSliceActions {
  setAnimationSpeed: (speed: number) => void;
  setMasterVolume: (volume: number) => void;
  setEffectsVolume: (volume: number) => void;
}

export interface SoundSliceState {
  lastSoundEffect: string | null;
}

export interface SoundSliceActions {
  clearLastSoundEffect: () => void;
}

// --- Combined Store Type ---

export type GameStoreState = GameStateSliceState &
  ItemSliceState &
  UISliceState &
  SettingsSliceState &
  SoundSliceState &
  GameStateSliceActions &
  ItemSliceActions &
  UISliceActions &
  SettingsSliceActions &
  SoundSliceActions;

// Type for the Zustand creator function's arguments
export type GameStoreCreator = (
  set: import("zustand").StoreApi<GameStoreState>["setState"],
  get: import("zustand").StoreApi<GameStoreState>["getState"],
  api: import("zustand").StoreApi<GameStoreState>
) => GameStoreState; // Or combine slice types directly if preferred

// Type for individual slice creators
export type SliceCreator<T> = (
  set: import("zustand").StoreApi<GameStoreState>["setState"],
  get: import("zustand").StoreApi<GameStoreState>["getState"]
) => T;
