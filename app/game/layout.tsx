"use client";

import { Box, Flex, useDisclosure } from "@chakra-ui/react";
import { ReactNode, useState, useCallback, useEffect } from "react";
import { GameHeader } from "@/components/layout/GameHeader";
import { GameFooter } from "@/components/layout/GameFooter";
import { SettingsModal } from "@/components/layout/SettingsModal";
import { InventoryModal } from "@/components/game/InventoryModal";
import { useSoundManager } from "@/hooks/useSoundManager"; // Import the sound hook
import { useNotifications } from "@/hooks/useNotifications"; // Use our notification hook

// Import Types
import { PlayerStatsData, Item } from "@/types/game.d";

// --- Placeholder Data (Replace with Zustand/Context Store) ---
const initialPlayerStats: PlayerStatsData = {
  currentHp: 85,
  maxHp: 100,
  gold: 120,
  xp: 150,
  maxXp: 500,
  level: 3,
};

const initialInventory: Item[] = [
  {
    id: "1",
    name: "Rusty Sword",
    description: "Barely holds an edge.",
    quantity: 1,
    rarity: "common",
    canEquip: true,
    canDrop: true,
  },
  {
    id: "2",
    name: "Health Potion",
    description: "Restores a small amount of health.",
    quantity: 3,
    rarity: "uncommon",
    canUse: true,
    canDrop: true,
  },
  {
    id: "3",
    name: "Mystic Gem",
    description: "Glows faintly.",
    quantity: 1,
    rarity: "rare",
    canDrop: true,
  },
  {
    id: "4",
    name: "Gold Coin",
    description: "Shiny!",
    quantity: 120,
    rarity: "common",
  }, // Non-interactive example
];
// --- End Placeholder Data ---

interface GameLayoutProps {
  children: ReactNode;
}

export default function GameLayout({ children }: GameLayoutProps) {
  // --- State Management (Placeholders) ---
  const [isProcessing, setIsProcessing] = useState(false);
  const [playerStats, setPlayerStats] =
    useState<PlayerStatsData>(initialPlayerStats);
  const [inventoryItems, setInventoryItems] =
    useState<Item[]>(initialInventory);
  // Example: We'll pass this down to GamePage to control animation
  const [animationSpeed, setAnimationSpeed] = useState(30); // Default speed (chars per second)

  // --- Hooks ---
  const { notifySuccess, notifyError, notifyInfo } = useNotifications();
  const {
    playSound,
    masterVolume,
    setMasterVolume,
    effectsVolume,
    setEffectsVolume,
    // musicVolume, setMusicVolume, // Add if using music
    // uiVolume, setUiVolume, // Add if distinguishing UI sounds
    isMuted,
    toggleMute,
    isInitialized: soundSystemReady, // Check if sounds are loaded
  } = useSoundManager();

  // Disclosure hooks for modals
  const {
    isOpen: isSettingsOpen,
    onOpen: onSettingsOpen,
    onClose: onSettingsClose,
  } = useDisclosure();
  const {
    isOpen: isInventoryOpen,
    onOpen: onInventoryOpen,
    onClose: onInventoryClose,
  } = useDisclosure();

  // Effect to play sound once system is ready (example)
  useEffect(() => {
    if (soundSystemReady) {
      // playSound('ui_start'); // Optional: Play a sound when game loads/sounds ready
      console.log("Sound System Ready!");
    }
  }, [soundSystemReady, playSound]);

  // --- Event Handlers (Placeholders - Connect to API/State Logic) ---
  const handleCommandSubmit = useCallback(
    async (command: string) => {
      if (isProcessing) return;

      console.log("Command submitted:", command);
      playSound("ui_click", true); // Play UI click sound, force restart if already playing
      setIsProcessing(true);

      // TODO: >>> Send command to Flask backend API <<<
      // const response = await apiClient.sendCommand(command);

      // --- Simulate API response ---
      await new Promise((resolve) => setTimeout(resolve, 1500)); // Simulate delay
      const wasSuccessful = Math.random() > 0.2; // Simulate success/failure
      let feedbackMessage = `Executed: ${command}`;
      let soundToPlay: string | null = null;
      // --- End Simulation ---

      // TODO: >>> Update state based on ACTUAL API response <<<
      if (wasSuccessful) {
        // Example updates: Modify description (passed to page), stats, inventory
        setPlayerStats((prev) => ({
          ...prev,
          gold: prev.gold + 5,
          currentHp: Math.max(0, prev.currentHp - 2),
        }));
        notifySuccess("Action Successful", `You ${command}.`); // Use notification hook
        feedbackMessage += " (Success)";
        // Simulate finding an item sometimes
        if (Math.random() > 0.8) {
          soundToPlay = "coin"; // Play coin sound if gold increased significantly or item found
          const newItem: Item = {
            id: Date.now().toString(),
            name: "Found Pebble",
            description: "A smooth pebble.",
            quantity: 1,
            rarity: "common",
            canDrop: true,
          };
          setInventoryItems((prev) => [...prev, newItem]);
          notifyInfo("Item Found!", `You found a ${newItem.name}`);
        } else {
          // soundToPlay = 'step'; // Example: play step sound on move
        }
      } else {
        notifyError(
          "Action Failed",
          `Something prevented you from ${command}.`
        );
        setPlayerStats((prev) => ({
          ...prev,
          currentHp: Math.max(0, prev.currentHp - 5),
        })); // Example: Take damage on failure
        feedbackMessage += " (Failed)";
        soundToPlay = "hit"; // Play hit sound on failure/damage
      }

      // Play sound based on outcome
      if (soundToPlay) {
        playSound(soundToPlay);
      }

      // Update game log (if using EventLog component)
      // setLogs(prev => [...prev, { id: Date.now(), text: feedbackMessage, type: wasSuccessful ? 'system' : 'error' }]);

      // TODO: Update description based on API response (likely pass setDescription down to GamePage)
      setIsProcessing(false);
    },
    [isProcessing, playSound, notifySuccess, notifyError, notifyInfo]
  ); // Add dependencies

  const handleUseItem = useCallback(
    (itemId: string) => {
      const item = inventoryItems.find((i) => i.id === itemId);
      if (!item || !item.canUse) return;

      console.log(`Using item: ${item.name}`);
      playSound("ui_click"); // Or a specific 'use_item' sound

      // TODO: API call to use item

      // Simulate effect & remove one item
      if (item.name.toLowerCase().includes("health potion")) {
        setPlayerStats((prev) => ({
          ...prev,
          currentHp: Math.min(prev.maxHp, prev.currentHp + 20),
        }));
        notifySuccess("Used Health Potion", "You feel a bit better.");
      }
      setInventoryItems((prev) =>
        prev
          .map((i) =>
            i.id === itemId ? { ...i, quantity: i.quantity - 1 } : i
          )
          .filter((i) => i.quantity > 0)
      );
      onInventoryClose(); // Close inventory after use
    },
    [inventoryItems, playSound, notifySuccess, onInventoryClose]
  ); // Add dependencies

  const handleDropItem = useCallback(
    (itemId: string) => {
      const item = inventoryItems.find((i) => i.id === itemId);
      if (!item || !item.canDrop) return;

      console.log(`Dropping item: ${item.name}`);
      playSound("ui_click"); // Or a specific 'drop_item' sound

      // TODO: API call to drop item

      // Simulate drop (remove from inventory)
      setInventoryItems((prev) => prev.filter((i) => i.id !== itemId));
      notifyInfo("Item Dropped", `You dropped ${item.name}.`);
      // Note: Don't close inventory automatically on drop maybe? User might drop multiple.
    },
    [inventoryItems, playSound, notifyInfo]
  );

  const handleEquipItem = useCallback(
    (itemId: string) => {
      const item = inventoryItems.find((i) => i.id === itemId);
      if (!item || !item.canEquip) return;
      console.log(`Equipping item: ${item.name}`);
      playSound("ui_click"); // Or a specific 'equip_item' sound
      // TODO: API call to equip item & update player stats (attack/defense)
      notifySuccess("Item Equipped", `You equipped ${item.name}.`);
      // May need visual feedback on player stats or avatar later
      onInventoryClose();
    },
    [inventoryItems, playSound, notifySuccess, onInventoryClose]
  );

  // Handler for animation speed change from Settings
  const handleAnimationSpeedChange = useCallback(
    (speed: number) => {
      setAnimationSpeed(speed);
      // Persist this setting (e.g., to localStorage or backend profile)
      localStorage.setItem("animationSpeed", speed.toString());
      notifyInfo(
        "Settings updated",
        `Text speed set to ${speed === 0 ? "Instant" : speed + " cps"}.`
      );
    },
    [notifyInfo]
  );

  const handleLookAction = () => {
    // Implement look action logic here
    console.log("Look action triggered");
  };

  // Load animation speed from localStorage on mount
  useEffect(() => {
    const savedSpeed = localStorage.getItem("animationSpeed");
    if (savedSpeed !== null) {
      setAnimationSpeed(parseInt(savedSpeed, 10));
    }
  }, []);

  return (
    <Flex
      direction="column"
      minH="100vh"
      bg="brand.bgDark"
      color="brand.textLight"
    >
      <GameHeader
        playerStats={playerStats}
        onOpenSettings={onSettingsOpen} // Pass the open handlers
        onOpenInventory={onInventoryOpen}
      />

      <Box
        as="main"
        flex="1"
        p={4}
        display="flex"
        flexDirection="column"
        overflow="hidden"
      >
        {/* Pass necessary state/functions down to children (GamePage) */}
        {/* Example: Cloning child to pass props, or use Context */}
        {/* {React.cloneElement(children as React.ReactElement, { animationSpeed })} */}
        {/* Simpler: Let GamePage manage its own state or use context */}
        {children}
      </Box>

      <GameFooter
        onCommandSubmit={handleCommandSubmit}
        isProcessingCommand={isProcessing}
        onInventoryAction={onInventoryOpen}
        onLookAction={handleLookAction}
      />

      {/* Render Modals */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={onSettingsClose}
        // Pass sound state and handlers
        masterVolume={masterVolume}
        onMasterVolumeChange={setMasterVolume}
        effectsVolume={effectsVolume}
        onEffectsVolumeChange={setEffectsVolume}
        // Add music/UI volumes if implemented
        // Pass animation speed state and handler
        animationSpeed={animationSpeed}
        onAnimationSpeedChange={handleAnimationSpeedChange}
      />

      <InventoryModal
        isOpen={isInventoryOpen}
        onClose={onInventoryClose}
        items={inventoryItems}
        onUseItem={handleUseItem}
        onEquipItem={handleEquipItem}
        onDropItem={handleDropItem}
      />
    </Flex>
  );
}
