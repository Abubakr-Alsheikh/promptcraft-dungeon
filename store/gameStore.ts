import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { PlayerStatsData, Item, LogEntry } from "@/types/game";
import { apiClient } from "@/lib/apiClient";
import { useNotificationStore } from "@/hooks/useNotifications";

// Define the state shape
interface GameState {
  // Core Game Data
  playerStats: PlayerStatsData | null;
  inventory: Item[];
  description: string;
  logs: LogEntry[]; // Optional event log state

  // UI / Meta State
  isProcessingCommand: boolean; // Loading state for backend actions
  isLoadingInitialData: boolean;
  isInventoryOpen: boolean;
  isSettingsOpen: boolean;
  animationSpeed: number; // Characters per second (0 for instant)

  // Sound State (managed by useSoundManager, but reflected here for settings)
  masterVolume: number; // 0-100
  effectsVolume: number; // 0-100
  // musicVolume: number; // 0-100 (if implemented)
}

// Define the actions
interface GameActions {
  // Initialization
  loadInitialData: () => Promise<void>;

  // Core Gameplay
  sendCommand: (command: string) => Promise<void>; // Connects to backend
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
  // setMusicVolume: (volume: number) => void;

  // Internal helpers (optional, not exposed directly if logic is within actions)
  _addLog: (log: Omit<LogEntry, "id" | "timestamp">) => void;
}

// --- Placeholder Initial State ---
const initialGameState: GameState = {
  playerStats: null,
  inventory: [],
  description: "Loading your adventure...",
  logs: [],
  isProcessingCommand: false,
  isLoadingInitialData: true,
  isInventoryOpen: false,
  isSettingsOpen: false,
  animationSpeed: 30, // Default speed
  masterVolume: 70,
  effectsVolume: 80,
};
// --- End Placeholder Initial State ---

// Create the store
export const useGameStore = create<GameState & GameActions>()(
  // Use persist middleware selectively for settings
  persist(
    (set, get) => ({
      ...initialGameState,

      // --- Actions Implementation ---

      loadInitialData: async () => {
        set({ isLoadingInitialData: true });
        try {
          // TODO: Replace with actual API call
          // const initialState = await apiClient.getInitialState();
          await new Promise((res) => setTimeout(res, 500)); // Simulate API call
          const initialState = {
            // Simulated response
            playerStats: {
              currentHp: 90,
              maxHp: 100,
              gold: 50,
              xp: 0,
              maxXp: 100,
              level: 1,
            },
            inventory: [
              {
                id: "1",
                name: "Health Potion",
                description: "Restores HP.",
                quantity: 2,
                rarity: "uncommon",
                canUse: true,
                canDrop: true,
              } as Item,
            ],
            description:
              "You awaken in a dimly lit stone cell. The air is cold and damp.",
          };

          set({
            playerStats: initialState.playerStats,
            inventory: initialState.inventory,
            description: initialState.description,
            isLoadingInitialData: false,
            logs: [{ id: 0, type: "system", text: "Game loaded." }],
          });
        } catch (error) {
          console.error("Failed to load initial game data:", error);
          set({
            description: "Error loading game data. Please refresh.",
            isLoadingInitialData: false,
            logs: [{ id: 0, type: "error", text: "Failed to load game data." }],
          });
        }
      },

      sendCommand: async (command) => {
        if (get().isProcessingCommand) return; // Prevent concurrent commands

        const { notifySuccess, notifyError } = useNotificationStore.getState();
        const previousDescription = get().description; // Store previous description for potential rollback or comparison

        set({
          isProcessingCommand: true,
          description:
            "Processing..." /* Optional: Clear description or show loading */,
        });
        get()._addLog({ type: "player", text: `> ${command}` }); // Use internal helper

        try {
          // TODO: Replace with actual API call
          // const result = await apiClient.sendCommand(command);
          await new Promise((res) =>
            setTimeout(res, 1000 + Math.random() * 1000)
          ); // Simulate
          const result = {
            // Simulated API Response Structure
            success: Math.random() > 0.2,
            message: `You attempted to "${command}".`,
            description: `The room looks slightly different after you tried to "${command}". A strange noise echoes.`,
            playerStats: {
              ...get().playerStats!,
              currentHp: Math.max(
                0,
                get().playerStats!.currentHp - (Math.random() > 0.5 ? 5 : 0)
              ),
              gold: get().playerStats!.gold + (Math.random() > 0.8 ? 10 : 0),
            }, // Simulate stat changes
            updatedInventory:
              Math.random() > 0.9
                ? [
                    ...get().inventory,
                    {
                      id: Date.now().toString(),
                      name: "Odd Stone",
                      description: "Feels warm.",
                      quantity: 1,
                      rarity: "common",
                      canDrop: true,
                    } as Item,
                  ]
                : get().inventory, // Simulate finding item
            soundEffect: Math.random() > 0.5 ? "hit" : "step", // Simulate sound effect name
          };

          if (result.success) {
            notifySuccess("Action Result", result.message);
            set({
              description: result.description,
              playerStats: result.playerStats,
              inventory: result.updatedInventory,
              // soundToPlay: result.soundEffect // Need sound manager integration
            });
            get()._addLog({ type: "narration", text: result.message });
          } else {
            notifyError("Action Failed", result.message);
            set({
              description: result.description, // Or maybe revert description: previousDescription,
              playerStats: result.playerStats, // Update stats even on failure (e.g., take damage)
              // soundToPlay: 'error_sound' // Need sound manager integration
            });
            get()._addLog({ type: "error", text: result.message });
          }
          // TODO: Trigger sound effect based on result.soundEffect using sound manager
        } catch (error) {
          console.error("Error sending command:", error);
          notifyError("API Error", "Failed to communicate with the server.");
          set({ description: previousDescription }); // Revert description on API error
          get()._addLog({
            type: "error",
            text: "Server communication failed.",
          });
        } finally {
          set({ isProcessingCommand: false });
        }
      },

      // --- Item Actions (Simplified simulation - add API calls) ---
      useItem: async (itemId) => {
        const item = get().inventory.find((i) => i.id === itemId);
        if (!item || !item.canUse || get().isProcessingCommand) return;
        set({ isProcessingCommand: true });
        console.log(`Simulating use item: ${item.name}`);
        get()._addLog({ type: "system", text: `Using ${item.name}...` });
        await new Promise((res) => setTimeout(res, 500));
        // TODO: API Call await apiClient.useItem(itemId);
        // Simulate effect
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

        set({
          inventory: updatedInventory,
          playerStats: newStats,
          isProcessingCommand: false,
        });
        useNotificationStore
          .getState()
          .notifySuccess("Item Used", `Used ${item.name}.`);
        // TODO: Play sound
        get().toggleInventory(false); // Close inventory after use
      },
      equipItem: async (itemId) => {
        /* Similar structure: check, set loading, API call, update state, notify, sound */
      },
      dropItem: async (itemId) => {
        /* Similar structure */
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

      // --- Settings Actions (called by useSoundManager setters or SettingsModal directly) ---
      setAnimationSpeed: (speed) => set({ animationSpeed: speed }),
      setMasterVolume: (volume) => set({ masterVolume: volume }),
      setEffectsVolume: (volume) => set({ effectsVolume: volume }),

      // --- Internal log helper ---
      _addLog: (logData) => {
        const newLog: LogEntry = {
          ...logData,
          id: Date.now() + Math.random(), // Simple unique enough ID
          timestamp: new Date(),
        };
        // Keep logs array from growing indefinitely
        const maxLogs = 50;
        set((state) => ({ logs: [...state.logs, newLog].slice(-maxLogs) }));
      },
    }),
    {
      name: "promptcraft-settings", // Name for localStorage key
      storage: createJSONStorage(() => localStorage), // Use localStorage
      partialize: (state) => ({
        // Only persist specific settings
        animationSpeed: state.animationSpeed,
        masterVolume: state.masterVolume,
        effectsVolume: state.effectsVolume,
        // musicVolume: state.musicVolume,
      }),
    }
  )
);

// --- Optional: Trigger initial data load ---
// This ensures data starts loading as soon as the store is imported.
// Alternatively, call loadInitialData() in a useEffect in _app.tsx or layout.tsx.
if (typeof window !== "undefined") {
  useGameStore.getState().loadInitialData();
}
