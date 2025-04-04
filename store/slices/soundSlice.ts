import {
  SoundSliceState,
  SoundSliceActions,
  SliceCreator,
} from "@/types/gameStore";

const initialSoundSliceState: SoundSliceState = {
  lastSoundEffect: null,
};

export const createSoundSlice: SliceCreator<
  SoundSliceState & SoundSliceActions
> = (set, get) => ({
  ...initialSoundSliceState,

  clearLastSoundEffect: () => set({ lastSoundEffect: null }),

  // Note: Setting 'lastSoundEffect' is done within other actions (sendCommand, useItem)
  // by calling set({ lastSoundEffect: 'sound_name' })
});
