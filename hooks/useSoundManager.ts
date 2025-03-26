import { useState, useEffect, useCallback, useRef } from "react";
import { Howl, Howler } from "howler";

// Define sound types/groups if needed for volume control
type SoundType = "effect" | "music" | "ui";

// Define the structure for sound definitions
interface SoundDefinition {
  name: string;
  src: string[]; // Array of paths for browser compatibility (e.g., ['/sounds/coin.webm', '/sounds/coin.mp3'])
  type: SoundType;
  volume?: number; // Default volume for this sound (0-1)
  loop?: boolean;
}

// --- Define Your Sounds Here ---
// Place sound files in /public/sounds/
const SOUNDS: SoundDefinition[] = [
  //   { name: "coin", src: ["/sounds/coin.wav"], type: "effect", volume: 0.6 },
  //   { name: "hit", src: ["/sounds/hit.wav"], type: "effect", volume: 0.8 },
  //   {
  //     name: "step",
  //     src: ["/sounds/step.ogg"],
  //     type: "effect",
  //     volume: 0.4,
  //     loop: true,
  //   }, // Example loop
  //   { name: "ui_click", src: ["/sounds/click.wav"], type: "ui", volume: 0.5 },
  //   {
  //     name: "open_chest",
  //     src: ["/sounds/chest.wav"],
  //     type: "effect",
  //     volume: 0.7,
  //   },
  // Add more sounds as needed (background music, monster growls, etc.)
  // { name: 'dungeon_music', src: ['/sounds/ambient_music.mp3'], type: 'music', volume: 0.3, loop: true },
];

// Store Howl instances
type SoundMap = Map<string, { howl: Howl; type: SoundType }>;

export function useSoundManager() {
  const soundsRef = useRef<SoundMap>(new Map());
  const [isInitialized, setIsInitialized] = useState(false);
  const [masterVolume, setMasterVolumeState] = useState(0.7); // Default master volume (0-1)
  const [effectsVolume, setEffectsVolumeState] = useState(1.0); // Multiplier for effects (0-1)
  const [musicVolume, setMusicVolumeState] = useState(1.0); // Multiplier for music (0-1)
  const [uiVolume, setUiVolumeState] = useState(1.0); // Multiplier for UI sounds (0-1)
  const [isMuted, setIsMuted] = useState(false);

  // --- Initialization ---
  useEffect(() => {
    console.log("Initializing Sound Manager...");
    SOUNDS.forEach((soundDef) => {
      const howl = new Howl({
        src: soundDef.src,
        volume: soundDef.volume ?? 1.0, // Use default sound volume initially
        loop: soundDef.loop ?? false,
        onload: () => {
          console.log(`Sound loaded: ${soundDef.name}`);
        },
        onloaderror: (id, err) => {
          console.error(`Error loading sound ${soundDef.name}:`, err);
        },
        // Apply initial volume based on type and master (handled by applyAllVolumes)
      });
      soundsRef.current.set(soundDef.name, { howl, type: soundDef.type });
    });
    applyAllVolumes(); // Apply initial volumes after loading setup
    Howler.mute(isMuted); // Apply initial mute state
    setIsInitialized(true);

    // Cleanup on unmount
    return () => {
      console.log("Unloading sounds...");
      Howler.unload(); // Unload all sounds
      soundsRef.current.clear();
      setIsInitialized(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount

  // --- Volume Application Logic ---
  const applyAllVolumes = useCallback(() => {
    Howler.volume(masterVolume); // Set global master volume

    soundsRef.current.forEach(({ howl, type }, name) => {
      let typeMultiplier = 1.0;
      switch (type) {
        case "effect":
          typeMultiplier = effectsVolume;
          break;
        case "music":
          typeMultiplier = musicVolume;
          break;
        case "ui":
          typeMultiplier = uiVolume;
          break;
      }
      // Find the original default volume defined for this sound
      const soundDef = SOUNDS.find((s) => s.name === name);
      const baseVolume = soundDef?.volume ?? 1.0;

      // Calculate final volume: Base * TypeMultiplier (Master is handled globally by Howler)
      // Howler's global volume acts as a ceiling, and individual sound volumes are relative to it.
      // So, we set the individual sound's volume directly.
      howl.volume(baseVolume * typeMultiplier);
      // console.log(`Set volume for ${name}: ${baseVolume} * ${typeMultiplier} = ${baseVolume * typeMultiplier} (Master: ${masterVolume})`);
    });
  }, [masterVolume, effectsVolume, musicVolume, uiVolume]);

  // --- Volume Control Effects ---
  useEffect(() => {
    if (!isInitialized) return;
    applyAllVolumes();
  }, [applyAllVolumes, isInitialized]); // Re-apply volumes when any volume state changes

  useEffect(() => {
    if (!isInitialized) return;
    Howler.mute(isMuted);
  }, [isMuted, isInitialized]);

  // --- Public API ---
  const playSound = useCallback(
    (name: string, forceRestart: boolean = false): number | null => {
      if (!isInitialized) {
        console.warn("Sound manager not initialized yet.");
        return null;
      }
      const sound = soundsRef.current.get(name);
      if (sound) {
        if (forceRestart && sound.howl.playing()) {
          sound.howl.stop();
        }
        if (!sound.howl.playing() || forceRestart) {
          const soundId = sound.howl.play();
          console.log(`Playing sound: ${name} (ID: ${soundId})`);
          return soundId;
        } else {
          // console.log(`Sound ${name} is already playing.`);
          return null; // Indicate already playing if not forcing restart
        }
      } else {
        console.warn(`Sound not found: ${name}`);
        return null;
      }
    },
    [isInitialized]
  );

  const stopSound = useCallback(
    (name: string, soundId?: number) => {
      if (!isInitialized) return;
      const sound = soundsRef.current.get(name);
      if (sound) {
        sound.howl.stop(soundId); // Stop specific instance or all instances
        console.log(`Stopped sound: ${name} (ID: ${soundId ?? "all"})`);
      } else {
        console.warn(`Sound not found for stopping: ${name}`);
      }
    },
    [isInitialized]
  );

  const setMasterVolume = useCallback((value: number) => {
    setMasterVolumeState(Math.max(0, Math.min(1, value / 100))); // Convert 0-100 to 0-1
  }, []);

  const setEffectsVolume = useCallback((value: number) => {
    setEffectsVolumeState(Math.max(0, Math.min(1, value / 100)));
  }, []);

  const setMusicVolume = useCallback((value: number) => {
    setMusicVolumeState(Math.max(0, Math.min(1, value / 100)));
  }, []);

  const setUiVolume = useCallback((value: number) => {
    setUiVolumeState(Math.max(0, Math.min(1, value / 100)));
  }, []);

  const toggleMute = useCallback(() => {
    setIsMuted((prev) => !prev);
  }, []);

  return {
    isInitialized,
    playSound,
    stopSound,
    masterVolume: masterVolume * 100, // Return as 0-100 for UI
    effectsVolume: effectsVolume * 100,
    musicVolume: musicVolume * 100,
    uiVolume: uiVolume * 100,
    isMuted,
    setMasterVolume,
    setEffectsVolume,
    setMusicVolume,
    setUiVolume,
    toggleMute,
  };
}
