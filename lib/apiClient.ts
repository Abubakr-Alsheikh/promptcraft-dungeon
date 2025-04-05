// lib/apiClient.ts
import { Item, PlayerStatsData } from "@/types/game";

// --- Request Payloads ---
interface StartGamePayload {
  playerName?: string;
  difficulty?: string;
}

interface SendCommandPayload {
  command: string;
  game_id: number;
}

// --- Response Structures (matching backend schemas) ---

// Base game state structure shared by responses
interface BaseGameStateResponse {
  playerStats: PlayerStatsData;
  inventory: Item[]; // Base expects 'inventory' key
  description: string; // Persistent room description
  roomTitle?: string | null; // Add room title (optional from backend)
  game_id: number;
}

// Specific response for the /start endpoint
// Inherits inventory, description, roomTitle, game_id from Base
export interface StartGameApiResponse extends BaseGameStateResponse {
  message: string; // Initial welcome message
}

// Specific response for the /command endpoint
// Inherits game_id from Base. Overrides others as needed.
export interface CommandApiResponse {
  success: boolean;
  message: string; // Action result message
  description: string; // Updated persistent room description
  playerStats: PlayerStatsData;
  updatedInventory: Item[]; // Command response specifically uses updatedInventory key
  roomTitle?: string | null; // Updated room title (optional)
  soundEffect?: string;
  game_id: number;
}

// Response for GET /state/:id
// Inherits inventory, description, roomTitle, game_id from Base
export interface GetStateApiResponse extends BaseGameStateResponse {
  message?: string;
}

// --- API Client Implementation ---

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001/api"; // Get from environment variables

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  let response: Response;
  try {
    response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        // Add authorization headers if needed
      },
      ...options,
    });

    const responseData = await response.json(); // Try to parse JSON regardless of status code

    if (!response.ok) {
      console.error(`API Error Response (${response.status}):`, responseData);
      // Prefer error message from backend if available
      const message =
        responseData?.message ||
        responseData?.error ||
        `HTTP error! Status: ${response.status}`;
      throw new Error(message);
    }

    return responseData as T;
  } catch (error) {
    console.error(
      `API request failed: ${options?.method || "GET"} ${url}`,
      error
    );
    // Re-throw the error potentially enriched from the response body
    throw error;
  }
}

export const apiClient = {
  // Start a new game
  startGame: (payload: StartGamePayload): Promise<StartGameApiResponse> => {
    console.log("apiClient.startGame sending:", payload);
    return request<StartGameApiResponse>("/game/start", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Send a player command
  sendCommand: (payload: SendCommandPayload): Promise<CommandApiResponse> => {
    console.log("apiClient.sendCommand sending:", payload);
    return request<CommandApiResponse>("/game/command", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Optional: Get current state by ID
  getGameState: (gameId: number): Promise<GetStateApiResponse> => {
    return request<GetStateApiResponse>(`/game/state/${gameId}`);
  },

  // Example stubs for item interactions (if needed)
  // useItem: (payload: { itemId: string; game_id: number }): Promise<CommandApiResponse> => {
  //   return apiClient.sendCommand({ command: `use ${payload.itemId}`, game_id: payload.game_id });
  // },
  // equipItem: (payload: { itemId: string; game_id: number }): Promise<CommandApiResponse> => {
  //   return apiClient.sendCommand({ command: `equip ${payload.itemId}`, game_id: payload.game_id });
  // },
  // dropItem: (payload: { itemId: string; game_id: number }): Promise<CommandApiResponse> => {
  //   return apiClient.sendCommand({ command: `drop ${payload.itemId}`, game_id: payload.game_id });
  // },
};
