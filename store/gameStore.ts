import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { GameStore } from "@/types/gameStore";

// Import slice creators
import { createGameStateSlice } from "./slices/gameStateSlice";
import { createItemSlice } from "./slices/itemSlice";
import { createUISlice } from "./slices/uiSlice";
import { createSettingsSlice } from "./slices/settingsSlice";
import { createSoundSlice } from "./slices/soundSlice";

export const useGameStore = create<GameStore>()(
  persist(
    (set, get, api) => ({
      // Combine slices by calling their creator functions
      ...createGameStateSlice(set, get),
      ...createItemSlice(set, get),
      ...createUISlice(set, get),
      ...createSettingsSlice(set, get),
      ...createSoundSlice(set, get),
      // Add any state/actions here that *don't* fit neatly into a slice (if any)
    }),
    {
      name: "promptcraft-settings", // Persistence key
      storage: createJSONStorage(() => localStorage),
      // Only persist settings and potentially the gameId for session resume
      partialize: (state) => ({
        gameId: state.gameId, // Persist gameId to allow resuming
        animationSpeed: state.animationSpeed,
        masterVolume: state.masterVolume,
        effectsVolume: state.effectsVolume,
        // Note: Don't persist transient state like isProcessingCommand, logs, description, etc.
      }),
      // onRehydrateStorage is optional, used for logging or side effects after hydration
      onRehydrateStorage: () => {
        console.log("Hydration from localStorage starting...");
        return (state, error) => {
          if (error) {
            console.error("Error rehydrating game store:", error);
          } else if (state) {
            console.log("Game store rehydrated successfully:", {
              gameId: state.gameId,
              animationSpeed: state.animationSpeed,
              masterVolume: state.masterVolume,
              effectsVolume: state.effectsVolume,
            });
            // Potential: If gameId exists, maybe fetch initial state?
            // Be careful not to overwrite state unnecessarily if starting fresh.
          }
        };
      },
      skipHydration: false, // Ensure hydration runs
    }
  )
);
