import { Item, PlayerStatsData } from "@/types/game";

// Define expected response structures from your Flask API
interface CommandResponse {
  success: boolean;
  message: string;
  description: string;
  playerStats: PlayerStatsData;
  updatedInventory: Item[];
  soundEffect?: string;
}

interface InitialStateResponse {
  playerStats: PlayerStatsData;
  inventory: Item[];
  description: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001/api"; // Get from environment variables

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        // Add authorization headers if needed
      },
      ...options,
    });

    if (!response.ok) {
      // Attempt to parse error body for more info
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        // Ignore if error body isn't JSON
      }
      console.error("API Error Response:", errorData);
      throw new Error(
        errorData?.message || `HTTP error! Status: ${response.status}`
      );
    }
    return (await response.json()) as T;
  } catch (error) {
    console.error(`API request failed: ${url}`, error);
    throw error; // Re-throw to be caught by Zustand action
  }
}

export const apiClient = {
  getInitialState: (): Promise<InitialStateResponse> => {
    return request<InitialStateResponse>("/game/state"); // Example endpoint
  },

  sendCommand: (command: string): Promise<CommandResponse> => {
    return request<CommandResponse>("/game/command", {
      method: "POST",
      body: JSON.stringify({ command }),
    });
  },

  useItem: (itemId: string): Promise<CommandResponse> => {
    return request<CommandResponse>("/game/item/use", {
      method: "POST",
      body: JSON.stringify({ itemId }),
    });
  },

  // Add equipItem, dropItem etc. similarly
};
