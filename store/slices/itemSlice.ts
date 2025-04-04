import {
  ItemSliceState,
  ItemSliceActions,
  SliceCreator,
} from "@/types/gameStore";
import { apiClient, CommandApiResponse } from "@/lib/apiClient"; // Assuming apiClient handles item actions
import { useNotificationStore } from "@/hooks/useNotifications";

export const createItemSlice: SliceCreator<
  ItemSliceState & ItemSliceActions
> = (set, get) => ({
  // No specific state owned by this slice initially

  useItem: async (itemId) => {
    const { gameId, inventory, isProcessingCommand } = get();
    const item = inventory.find((i) => i.id === itemId);
    if (!item || !item.canUse || isProcessingCommand || !gameId) return;

    console.log(
      `Attempting to use item: ${item.name} (ID: ${itemId}) in game ${gameId}`
    );
    get()._addLog({ type: "system", text: `Using ${item.name}...` });
    set({ isProcessingCommand: true, lastSoundEffect: null }); // Set loading, clear sound

    try {
      // TODO: Replace placeholder with actual API call when backend is ready
      // const response = await apiClient.useItem({ itemId, game_id: gameId });
      const response: CommandApiResponse = {
        // PLACEHOLDER RESPONSE
        success: true,
        message: `You used the ${item.name}. It feels refreshing!`,
        playerStats: {
          ...get().playerStats!,
          currentHp: Math.min(
            get().playerStats!.maxHp,
            get().playerStats!.currentHp + 10
          ),
        },
        updatedInventory: get()
          .inventory.map((i) =>
            i.id === itemId ? { ...i, quantity: i.quantity - 1 } : i
          )
          .filter((i) => i.quantity > 0),
        description: `A faint warmth spreads through you after using the ${item.name}.`,
        soundEffect: "potion_drink",
        game_id: gameId,
      };
      // END PLACEHOLDER

      if (response.success) {
        set({
          description: response.description,
          playerStats: response.playerStats,
          inventory: response.updatedInventory,
          lastSoundEffect: response.soundEffect || null,
        });
        get()._addLog({ type: "narration", text: response.message });
        useNotificationStore
          .getState()
          .notifySuccess("Item Used", response.message);
      } else {
        throw new Error(response.message || "Failed to use item.");
      }
    } catch (error: any) {
      console.error(`Error using item ${itemId}:`, error);
      get()._addLog({
        type: "error",
        text: `Failed to use ${item.name}: ${error.message}`,
      });
      useNotificationStore.getState().notifyError("Use Failed", error.message);
    } finally {
      set({ isProcessingCommand: false }); // Ensure loading state is cleared
      get().toggleInventory(false); // Close inventory modal
    }
  },

  equipItem: async (itemId) => {
    const { gameId, inventory, isProcessingCommand } = get();
    const item = inventory.find((i) => i.id === itemId);
    if (!item || !item.canEquip || isProcessingCommand || !gameId) return;

    console.warn(
      `Equip item functionality not fully implemented for: ${item.name}`
    );
    get()._addLog({
      type: "system",
      text: `Attempting to equip ${item.name}...`,
    });
    // TODO: set({ isProcessingCommand: true });
    try {
      // TODO: Implement API call: apiClient.equipItem({ itemId, game_id: gameId })
      // TODO: Handle CommandApiResponse to update state (stats, inventory - potentially marking equipped, description, sound)
      useNotificationStore
        .getState()
        .notifyInfo("Equip", "Equip action needs backend implementation.");
    } catch (error: any) {
      useNotificationStore
        .getState()
        .notifyError("Equip Failed", error.message);
    } finally {
      // TODO: set({ isProcessingCommand: false });
      get().toggleInventory(false);
    }
  },

  dropItem: async (itemId) => {
    const { gameId, inventory, isProcessingCommand } = get();
    const item = inventory.find((i) => i.id === itemId);
    if (!item || !item.canDrop || isProcessingCommand || !gameId) return;

    if (
      !window.confirm(
        `Are you sure you want to drop ${item.name}? It might be lost forever.`
      )
    ) {
      return;
    }

    console.warn(
      `Drop item functionality not fully implemented for: ${item.name}`
    );
    get()._addLog({
      type: "system",
      text: `Attempting to drop ${item.name}...`,
    });
    // TODO: set({ isProcessingCommand: true });
    try {
      // TODO: Implement API call: apiClient.dropItem({ itemId, quantity: item.quantity, game_id: gameId })
      // TODO: Handle CommandApiResponse (update inventory, description, sound)
      useNotificationStore
        .getState()
        .notifyInfo("Drop", "Drop action needs backend implementation.");
    } catch (error: any) {
      useNotificationStore.getState().notifyError("Drop Failed", error.message);
    } finally {
      // TODO: set({ isProcessingCommand: false });
      get().toggleInventory(false);
    }
  },
});
