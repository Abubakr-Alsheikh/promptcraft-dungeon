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
  roomTitle?: string | null;
  game_id: number;
}

// Specific response for the /start endpoint
export interface StartGameApiResponse extends BaseGameStateResponse {
  message: string;
  suggestedActions?: string[] | null;
  soundEffect?: string | null;
}

// Specific response for the /command endpoint
export interface CommandApiResponse {
  success: boolean;
  message: string;
  description: string;
  playerStats: PlayerStatsData;
  updatedInventory: Item[];
  roomTitle?: string | null;
  soundEffect?: string | null;
  game_id: number;
  suggestedActions?: string[] | null;
  difficulty?: string | null;
  roomsCleared?: number | null;
}

// Response for GET /state/:id
export interface GetStateApiResponse extends BaseGameStateResponse {
  message?: string;
  soundEffect?: string | null;
}

// --- API Client Implementation ---

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001/api";

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  let response: Response;
  try {
    response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
      },
      ...options,
    });

    const responseData = await response.json();

    if (!response.ok) {
      console.error(`API Error Response (${response.status}):`, responseData);
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
    throw error;
  }
}

export const apiClient = {
  startGame: (payload: StartGamePayload): Promise<StartGameApiResponse> => {
    console.log("apiClient.startGame sending:", payload);
    return request<StartGameApiResponse>("/game/start", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  sendCommand: (payload: SendCommandPayload): Promise<CommandApiResponse> => {
    console.log("apiClient.sendCommand sending:", payload);
    return request<CommandApiResponse>("/game/command", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getGameState: (gameId: number): Promise<GetStateApiResponse> => {
    return request<GetStateApiResponse>(`/game/state/${gameId}`);
  },
};
