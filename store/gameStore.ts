import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { PlayerStatsData, Item, LogEntry } from "@/types/game";
import {
  apiClient,
  StartGameApiResponse,
  CommandApiResponse,
} from "@/lib/apiClient";
import { useNotificationStore } from "@/hooks/useNotifications";

// Define the state shape
interface GameState {
  // Core Game Data
  gameId: number | null; // Added to store the ID from the backend
  playerStats: PlayerStatsData | null;
  inventory: Item[];
  description: string;
  logs: LogEntry[];

  // UI / Meta State
  isStartingGame: boolean; // More specific loading state for start
  isProcessingCommand: boolean;
  isInventoryOpen: boolean;
  isSettingsOpen: boolean;
  animationSpeed: number;
  masterVolume: number;
  effectsVolume: number;
}

// Define the actions
interface GameActions {
  startGame: (playerName: string, difficulty: string) => Promise<boolean>; // Returns true on success, false on error
  // Core Gameplay
  sendCommand: (command: string) => Promise<void>;
  useItem: (itemId: string) => Promise<void>;
  equipItem: (itemId: string) => Promise<void>;
  dropItem: (itemId: string) => Promise<void>;

  // UI Control
  toggleInventory: (open?: boolean) => void;
  toggleSettings: (open?: boolean) => void;

  // Settings Persistence
  setAnimationSpeed: (speed: number) => void;
  setMasterVolume: (volume: number) => void;
  setEffectsVolume: (volume: number) => void;
  _addLog: (log: Omit<LogEntry, "id" | "timestamp">) => void;
  resetGameState: () => void; // Action to reset state for a new game
}

const initialGameState: Omit<
  GameState, // Persisted settings are handled by persist middleware
  "animationSpeed" | "masterVolume" | "effectsVolume"
> = {
  gameId: null, // Start with no game ID
  playerStats: null,
  inventory: [],
  description: "Prepare for your adventure...", // Initial placeholder before start
  logs: [],
  isStartingGame: false,
  isProcessingCommand: false,
  isInventoryOpen: false,
  isSettingsOpen: false,
};

export const useGameStore = create<GameState & GameActions>()(
  persist(
    (set, get) => ({
      ...initialGameState, // Non-persisted initial state
      // Persisted state defaults (will be overwritten by localStorage if present)
      animationSpeed: 30,
      masterVolume: 70,
      effectsVolume: 80,

      // --- Actions Implementation ---

      startGame: async (playerName, difficulty) => {
        const { notifySuccess, notifyError } = useNotificationStore.getState();
        set({ isStartingGame: true, description: "Generating your world..." });
        get()._addLog({ type: "system", text: "Starting new game..." });

        try {
          const response: StartGameApiResponse = await apiClient.startGame({
            playerName: playerName || undefined, // Send undefined if empty, backend uses default
            difficulty: difficulty,
          });

          console.log("startGame response received:", response);

          set({
            gameId: response.game_id, // Store the game ID!
            playerStats: response.playerStats,
            inventory: response.inventory,
            description: response.description,
            isStartingGame: false,
            logs: [
              // Reset logs for new game
              { id: 0, type: "system", text: response.message },
              { id: 1, type: "narration", text: response.description },
            ],
          });
          notifySuccess("Game Started!", response.message);
          return true; // Indicate success
        } catch (error: any) {
          console.error("Failed to start game:", error);
          const errorMessage =
            error.message ||
            "Failed to start game. Check connection or server.";
          notifyError("Error Starting Game", errorMessage);
          set({
            description: `Error: ${errorMessage}. Please try again.`,
            isStartingGame: false,
            gameId: null, // Ensure gameId is null on error
          });
          get()._addLog({
            type: "error",
            text: `Failed to start: ${errorMessage}`,
          });
          return false; // Indicate failure
        }
      },

      sendCommand: async (command) => {
        const { gameId, isProcessingCommand } = get();
        if (isProcessingCommand) return;
        if (!gameId) {
          console.error("Cannot send command: gameId is null.");
          get()._addLog({
            type: "error",
            text: "Error: No active game session.",
          });
          return;
        }

        const { notifySuccess, notifyError } = useNotificationStore.getState();
        const previousDescription = get().description;

        set({ isProcessingCommand: true });
        get()._addLog({ type: "player", text: `> ${command}` });

        try {
          // Pass gameId to the API client
          const result: CommandApiResponse = await apiClient.sendCommand({
            command,
            game_id: gameId,
          });

          console.log("sendCommand response received:", result);

          if (result.success) {
            // Update state with results
            set({
              description: result.description,
              playerStats: result.playerStats,
              inventory: result.updatedInventory, // Use the correct key from response
              isProcessingCommand: false,
            });
            get()._addLog({ type: "narration", text: result.message });
            // Optional: Play sound effect via sound manager using result.soundEffect
            notifySuccess("Action", result.message); // Simple notification for action message
          } else {
            // Handle structured failure from backend
            notifyError(
              "Action Failed",
              result.message || "The attempt failed."
            );
            set({
              description: result.description || previousDescription, // Show AI's description of failure, or revert
              playerStats: result.playerStats, // Update stats even on failure
              inventory: result.updatedInventory, // Update inventory even on failure
              isProcessingCommand: false,
            });
            get()._addLog({
              type: "error",
              text: result.message || "Action failed.",
            });
          }
        } catch (error: any) {
          console.error("Error sending command:", error);
          const errorMessage =
            error.message || "Failed to communicate with the server.";
          notifyError("API Error", errorMessage);
          set({
            description: previousDescription, // Revert description on API error
            isProcessingCommand: false,
          });
          get()._addLog({
            type: "error",
            text: `Server communication failed: ${errorMessage}`,
          });
        }
      },

      // --- Item Actions (Needs gameId passed to apiClient) ---
      useItem: async (itemId) => {
        const { gameId, inventory, isProcessingCommand } = get();
        const item = inventory.find((i) => i.id === itemId);
        if (!item || !item.canUse || isProcessingCommand || !gameId) return;

        // TODO: Implement API Call like:
        // await apiClient.useItem({ itemId, game_id: gameId });
        // Then update state based on the CommandApiResponse

        console.warn("useItem API call not implemented yet.");
        get()._addLog({
          type: "system",
          text: `Attempted to use ${item.name} (offline simulation)`,
        });
        // Placeholder offline logic
        let newStats = get().playerStats;
        if (item.name.toLowerCase().includes("health potion")) {
          newStats = {
            ...newStats!,
            currentHp: Math.min(newStats!.maxHp, newStats!.currentHp + 20),
          };
        }
        const updatedInventory = get()
          .inventory.map((i) =>
            i.id === itemId ? { ...i, quantity: i.quantity - 1 } : i
          )
          .filter((i) => i.quantity > 0);
        set({ inventory: updatedInventory, playerStats: newStats });
        get().toggleInventory(false);
      },
      equipItem: async (itemId) => {
        /* TODO: Implement API Call */ console.warn(
          "equipItem not implemented"
        );
      },
      dropItem: async (itemId) => {
        /* TODO: Implement API Call */ console.warn("dropItem not implemented");
      },

      // --- UI Actions ---
      toggleInventory: (open) =>
        set((state) => ({
          isInventoryOpen: open !== undefined ? open : !state.isInventoryOpen,
        })),
      toggleSettings: (open) =>
        set((state) => ({
          isSettingsOpen: open !== undefined ? open : !state.isSettingsOpen,
        })),

      // --- Settings Actions ---
      setAnimationSpeed: (speed) => set({ animationSpeed: speed }),
      setMasterVolume: (volume) => set({ masterVolume: volume }),
      setEffectsVolume: (volume) => set({ effectsVolume: volume }),

      // --- Internal log helper ---
      _addLog: (logData) => {
        const newLog: LogEntry = {
          ...logData,
          id: Date.now() + Math.random(),
          timestamp: new Date(),
        };
        const maxLogs = 100; // Increased max logs
        set((state) => ({ logs: [...state.logs, newLog].slice(-maxLogs) }));
      },

      // --- Reset Game State ---
      resetGameState: () => {
        set({ ...initialGameState }); // Reset non-persisted state
        get()._addLog({ type: "system", text: "Game state reset." });
        console.log("Game state reset.");
      },
    }),
    {
      name: "promptcraft-settings",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        gameId: state.gameId,
        animationSpeed: state.animationSpeed,
        masterVolume: state.masterVolume,
        effectsVolume: state.effectsVolume,
      }),
      onRehydrateStorage: () => {
        console.log("Settings hydration finished.");
        return (state, error) => {
          if (error) {
            console.error("Error rehydrating settings:", error);
          } else if (state) {
            // You could potentially trigger actions based on rehydrated settings here
            // For example, applying the initial volume to the sound manager
            // Although the GameLayout effect already does this.
            console.log("Settings rehydrated:", {
              gameId: state.gameId,
              animationSpeed: state.animationSpeed,
              masterVolume: state.masterVolume,
              effectsVolume: state.effectsVolume,
            });
          }
        };
      },
    }
  )
);
