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
  inventory: Item[];
  description: string;
  game_id: number; // Include game_id in all relevant responses
}

// Specific response for the /start endpoint
export interface StartGameApiResponse extends BaseGameStateResponse {
  message: string;
}

// Specific response for the /command endpoint
export interface CommandApiResponse extends BaseGameStateResponse {
  success: boolean;
  message: string;
  updatedInventory: Item[]; // Command response specifically uses updatedInventory key
  soundEffect?: string;
}

// Response for GET /state/:id
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
  // NEW: Method to start a new game
  startGame: (payload: StartGamePayload): Promise<StartGameApiResponse> => {
    console.log("apiClient.startGame sending:", payload);
    return request<StartGameApiResponse>("/game/start", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // UPDATED: Method to send a command, now requires game_id
  sendCommand: (payload: SendCommandPayload): Promise<CommandApiResponse> => {
    console.log("apiClient.sendCommand sending:", payload);
    return request<CommandApiResponse>("/game/command", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Example: Add methods for item interaction (if needed, passing game_id)
  // useItem: (payload: { itemId: string; game_id: number }): Promise<CommandApiResponse> => {
  //   return request<CommandApiResponse>("/game/item/use", { // Example endpoint
  //     method: 'POST',
  //     body: JSON.stringify(payload),
  //   });
  // },

  // Optional: Method to get current state by ID
  getGameState: (gameId: number): Promise<GetStateApiResponse> => {
    return request<GetStateApiResponse>(`/game/state/${gameId}`);
  },
};
