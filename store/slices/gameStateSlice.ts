import {
  GameStateSliceState,
  GameStateSliceActions,
  SliceCreator,
} from "@/types/gameStore";
import { LogEntry } from "@/types/game";
import {
  apiClient,
  StartGameApiResponse,
  CommandApiResponse,
} from "@/lib/apiClient";
import { useNotificationStore } from "@/hooks/useNotifications";

// Initial state specific to this slice
const initialGameStateSliceState: GameStateSliceState = {
  gameId: null,
  playerStats: null,
  inventory: [],
  description: "Prepare for your adventure...",
  logs: [],
  isStartingGame: false,
  isProcessingCommand: false,
};

export const createGameStateSlice: SliceCreator<
  GameStateSliceState & GameStateSliceActions
> = (set, get) => ({
  ...initialGameStateSliceState,

  _addLog: (logData) => {
    const newLog: LogEntry = {
      ...logData,
      id: Date.now() + Math.random(),
      timestamp: new Date(),
    };
    const maxLogs = 100; // Increased max logs
    set((state) => ({ logs: [...state.logs, newLog].slice(-maxLogs) }));
  },

  resetGameState: () => {
    set({ ...initialGameStateSliceState, logs: [] }); // Reset state, clear logs
    get()._addLog({ type: "system", text: "Game state reset." }); // Use the internal log action
    console.log("Game state reset.");
  },

  startGame: async (playerName, difficulty) => {
    const { notifySuccess, notifyError } = useNotificationStore.getState();
    // Reset state *before* API call when starting a fresh game via UI
    // Note: resetGameState() is separate, called explicitly from HomePage now
    set({
      isStartingGame: true,
      description: "Generating your world...",
      logs: [], // Clear logs on new game start attempt
      gameId: null, // Ensure no stale gameId
      playerStats: null,
      inventory: [],
    });
    get()._addLog({ type: "system", text: "Starting new game..." });

    try {
      const response: StartGameApiResponse = await apiClient.startGame({
        playerName: playerName || undefined,
        difficulty: difficulty,
      });

      console.log("startGame response received:", response);

      set({
        gameId: response.game_id,
        playerStats: response.playerStats,
        inventory: response.inventory,
        description: response.description,
        isStartingGame: false,
      });
      // Add initial logs after successful start
      get()._addLog({ type: "system", text: response.message });
      get()._addLog({ type: "narration", text: response.description });

      notifySuccess("Game Started!", response.message);
      // set({ lastSoundEffect: null }); // Move sound logic to soundSlice/itemSlice
      return true; // Indicate success
    } catch (error: any) {
      console.error("Failed to start game:", error);
      const errorMessage =
        error.message || "Failed to start game. Check connection or server.";
      notifyError("Error Starting Game", errorMessage);
      set({
        description: `Error: ${errorMessage}. Please try again.`,
        isStartingGame: false,
        gameId: null, // Ensure gameId is null on error
        playerStats: null,
        inventory: [],
        logs: [], // Clear logs on error too
      });
      get()._addLog({
        type: "error",
        text: `Failed to start: ${errorMessage}`,
      });
      return false; // Indicate failure
    }
  },

  sendCommand: async (command) => {
    const { gameId, isProcessingCommand } = get(); // Get from full state
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
      const result: CommandApiResponse = await apiClient.sendCommand({
        command,
        game_id: gameId,
      });

      console.log("sendCommand response received:", result);

      set({
        description: result.description,
        playerStats: result.playerStats,
        inventory: result.updatedInventory,
        isProcessingCommand: false,
        // Update sound effect via set, handled by sound slice potentially
        lastSoundEffect: result.soundEffect || null,
      });

      if (result.success) {
        get()._addLog({ type: "narration", text: result.message });
        notifySuccess("Action", result.message);
      } else {
        // Handle structured failure from backend
        get()._addLog({
          type: "error",
          text: result.message || "Action failed.",
        });
        notifyError("Action Failed", result.message || "The attempt failed.");
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
});
