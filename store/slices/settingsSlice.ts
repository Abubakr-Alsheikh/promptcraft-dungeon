import {
  SettingsSliceState,
  SettingsSliceActions,
  SliceCreator,
} from "@/types/gameStore";

// These defaults will be potentially overridden by persisted state on hydration
const initialSettingsSliceState: SettingsSliceState = {
  animationSpeed: 30,
  masterVolume: 70,
  effectsVolume: 80,
};

export const createSettingsSlice: SliceCreator<
  SettingsSliceState & SettingsSliceActions
> = (set, get) => ({
  ...initialSettingsSliceState,

  setAnimationSpeed: (speed) => set({ animationSpeed: speed }),
  setMasterVolume: (volume) => set({ masterVolume: volume }),
  setEffectsVolume: (volume) => set({ effectsVolume: volume }),
});
