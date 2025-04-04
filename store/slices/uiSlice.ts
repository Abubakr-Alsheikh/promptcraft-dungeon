import { UISliceState, UISliceActions, SliceCreator } from "@/types/gameStore";

const initialUISliceState: UISliceState = {
  isInventoryOpen: false,
  isSettingsOpen: false,
};

export const createUISlice: SliceCreator<UISliceState & UISliceActions> = (
  set,
  get
) => ({
  ...initialUISliceState,

  toggleInventory: (open) =>
    set((state) => ({
      isInventoryOpen: open !== undefined ? open : !state.isInventoryOpen,
    })),

  toggleSettings: (open) =>
    set((state) => ({
      isSettingsOpen: open !== undefined ? open : !state.isSettingsOpen,
    })),
});
