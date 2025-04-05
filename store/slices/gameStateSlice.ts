// store/slices/gameStateSlice.ts
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
  roomTitle: null, // Initialize roomTitle
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
    const maxLogs = 100; // Keep max logs
    set((state) => ({ logs: [...state.logs, newLog].slice(-maxLogs) }));
  },

  resetGameState: () => {
    set({
      ...initialGameStateSliceState,
      logs: [], // Clear logs explicitly on reset
      roomTitle: null, // Reset roomTitle
    });
    get()._addLog({ type: "system", text: "Game state reset." });
    console.log("Game state reset.");
  },

  startGame: async (playerName, difficulty) => {
    const { notifySuccess, notifyError } = useNotificationStore.getState();
    set({
      isStartingGame: true,
      description: "Generating your world...",
      roomTitle: "Loading...", // Set initial title during load
      logs: [],
      gameId: null,
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
        inventory: response.inventory, // Use 'inventory' key from response
        description: response.description, // Set persistent description
        roomTitle: response.roomTitle || "Unknown Area", // Set room title, provide default
        isStartingGame: false,
      });
      // Add initial logs after successful start
      get()._addLog({ type: "system", text: response.message }); // Welcome message
      get()._addLog({ type: "narration", text: response.description }); // Initial room description log

      notifySuccess("Game Started!", response.message);
      return true; // Indicate success
    } catch (error: any) {
      console.error("Failed to start game:", error);
      const errorMessage =
        error.message || "Failed to start game. Check connection or server.";
      notifyError("Error Starting Game", errorMessage);
      set({
        description: `Error: ${errorMessage}. Please try again.`,
        roomTitle: "Error", // Indicate error in title
        isStartingGame: false,
        gameId: null,
        playerStats: null,
        inventory: [],
        logs: [],
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
    // Store previous state in case of API error (optional, but good practice)
    const previousDescription = get().description;
    const previousRoomTitle = get().roomTitle;

    set({ isProcessingCommand: true });
    get()._addLog({ type: "player", text: `> ${command}` });

    try {
      const result: CommandApiResponse = await apiClient.sendCommand({
        command,
        game_id: gameId,
      });

      console.log("sendCommand response received:", result);

      // Update state based on successful response
      set({
        description: result.description, // Update persistent description
        roomTitle: result.roomTitle || previousRoomTitle || "Unknown Area", // Update title, keep previous if null, provide default
        playerStats: result.playerStats,
        inventory: result.updatedInventory, // Use 'updatedInventory' key
        isProcessingCommand: false,
        lastSoundEffect: result.soundEffect || null, // Handle sound effect
      });

      // Add the action result message to the log
      if (result.message) {
        get()._addLog({ type: "narration", text: result.message });
      }

      // Show notification based on success flag
      if (result.success) {
        // Use result.message for notification if available and meaningful
        notifySuccess("Action", result.message || "Action completed.");
      } else {
        // Handle structured failure from backend
        const failureMsg = result.message || "Action failed.";
        get()._addLog({ type: "error", text: failureMsg });
        notifyError("Action Failed", failureMsg);
      }
    } catch (error: any) {
      console.error("Error sending command:", error);
      const errorMessage =
        error.message || "Failed to communicate with the server.";
      notifyError("API Error", errorMessage);
      // Revert description/title on error? Optional.
      set({
        // description: previousDescription, // Option to revert
        // roomTitle: previousRoomTitle,   // Option to revert
        isProcessingCommand: false,
      });
      get()._addLog({
        type: "error",
        text: `Server communication failed: ${errorMessage}`,
      });
    }
  },
});
