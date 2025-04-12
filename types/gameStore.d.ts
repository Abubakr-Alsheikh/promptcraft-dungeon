import { PlayerStatsData, Item, LogEntry } from "@/types/game";

// --- Slice Interfaces (Define the shape of each part) ---

export interface GameStateSliceState {
  gameId: number | null;
  playerStats: PlayerStatsData | null;
  inventory: Item[];
  description: string;
  roomTitle: string | null;
  logs: LogEntry[];
  isStartingGame: boolean;
  isProcessingCommand: boolean;
  suggestedActions: string[] | null;
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

// --- UI Slice ---
export interface UISliceState {
  isInventoryOpen: boolean;
  isSettingsOpen: boolean;
}

export interface UISliceActions {
  toggleInventory: (open?: boolean) => void;
  toggleSettings: (open?: boolean) => void;
}

// --- Settings Slice ---
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

// --- Sound Slice ---
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
  SoundSliceState;

export type GameStoreActions = GameStateSliceActions &
  ItemSliceActions &
  UISliceActions &
  SettingsSliceActions &
  SoundSliceActions;

// --- Combined Store Interface ---
export type GameStore = GameStoreState & GameStoreActions;

// Type for the Zustand creator function's arguments
// Using GameStore for simpler type definition in create function
export type GameStoreCreator = (
  set: import("zustand").StoreApi<GameStore>["setState"],
  get: import("zustand").StoreApi<GameStore>["getState"],
  api: import("zustand").StoreApi<GameStore>
) => GameStore; // Should return the combined GameStore type

// Type for individual slice creators
// T represents the slice's state & actions combined
export type SliceCreator<T> = (
  set: import("zustand").StoreApi<GameStore>["setState"],
  get: import("zustand").StoreApi<GameStore>["getState"]
) => T;
