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
  roomTitle: null,
  logs: [],
  isStartingGame: false,
  isProcessingCommand: false,
  suggestedActions: null,
};

// Use the specific SliceCreator<T> type where T combines state and actions for this slice
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
    const maxLogs = 100;
    set((state) => ({ logs: [...state.logs, newLog].slice(-maxLogs) }));
  },

  resetGameState: () => {
    set({
      ...initialGameStateSliceState,
      logs: [], // Clear logs
      roomTitle: null, // Reset roomTitle
      suggestedActions: null, // Reset suggestions
    });
    get()._addLog({ type: "system", text: "Game state reset." });
    console.log("Game state reset.");
  },

  startGame: async (playerName, difficulty) => {
    const { notifySuccess, notifyError } = useNotificationStore.getState();
    set({
      isStartingGame: true,
      description: "Generating your world...",
      roomTitle: "Loading...",
      logs: [],
      gameId: null,
      playerStats: null,
      inventory: [],
      suggestedActions: null,
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
        roomTitle: response.roomTitle || "Unknown Area",
        isStartingGame: false,
        suggestedActions: response.suggestedActions || null,
        lastSoundEffect: response.soundEffect || null,
      });

      get()._addLog({ type: "system", text: response.message });
      get()._addLog({ type: "narration", text: response.description });

      notifySuccess("Game Started!", response.message);
      return true;
    } catch (error: any) {
      console.error("Failed to start game:", error);
      const errorMessage =
        error.message || "Failed to start game. Check connection or server.";
      notifyError("Error Starting Game", errorMessage);
      set({
        description: `Error: ${errorMessage}. Please try again.`,
        roomTitle: "Error",
        isStartingGame: false,
        gameId: null,
        playerStats: null,
        inventory: [],
        logs: [],
        suggestedActions: null,
      });
      get()._addLog({
        type: "error",
        text: `Failed to start: ${errorMessage}`,
      });
      return false;
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
    const previousSuggestions = get().suggestedActions;
    const previousDescription = get().description;
    const previousRoomTitle = get().roomTitle;

    set({ isProcessingCommand: true, suggestedActions: null });
    get()._addLog({ type: "player", text: `> ${command}` });

    try {
      const result: CommandApiResponse = await apiClient.sendCommand({
        command,
        game_id: gameId,
      });

      console.log("sendCommand response received:", result);

      set({
        description: result.description,
        roomTitle: result.roomTitle || previousRoomTitle || "Unknown Area",
        playerStats: result.playerStats,
        inventory: result.updatedInventory,
        isProcessingCommand: false,
        lastSoundEffect: result.soundEffect || null,
        suggestedActions: result.suggestedActions || null,
      });

      if (result.message) {
        get()._addLog({ type: "narration", text: result.message });
      }

      if (result.success) {
        notifySuccess("Action", result.message || "Action completed.");
      } else {
        const failureMsg = result.message || "Action failed.";
        get()._addLog({ type: "error", text: failureMsg });
        notifyError("Action Failed", failureMsg);
        set({ suggestedActions: previousSuggestions });
      }
    } catch (error: any) {
      console.error("Error sending command:", error);
      const errorMessage =
        error.message || "Failed to communicate with the server.";
      notifyError("API Error", errorMessage);
      set({
        description: previousDescription,
        roomTitle: previousRoomTitle,
        isProcessingCommand: false,
        suggestedActions: null,
      });
      get()._addLog({
        type: "error",
        text: `Server communication failed: ${errorMessage}`,
      });
    }
  },
});
