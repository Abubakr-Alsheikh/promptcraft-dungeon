"use client";

import { Box, Flex } from "@chakra-ui/react";
import { ReactNode, useEffect } from "react";
import { GameHeader } from "@/components/layout/GameHeader";
import { GameFooter } from "@/components/layout/GameFooter";
import { SettingsModal } from "@/components/layout/SettingsModal";
import { InventoryModal } from "@/components/game/InventoryModal";
import { useSoundManager } from "@/hooks/useSoundManager";
import { useGameStore } from "@/store/gameStore";

interface GameLayoutProps {
  children: ReactNode;
}

export default function GameLayout({ children }: GameLayoutProps) {
  // --- Get State and Actions from Zustand Store ---
  const {
    playerStats,
    inventory,
    isProcessingCommand,
    isInventoryOpen,
    isSettingsOpen,
    animationSpeed,
    masterVolume,
    effectsVolume,
    // Actions
    sendCommand,
    useItem,
    equipItem,
    dropItem,
    toggleInventory,
    toggleSettings,
    setAnimationSpeed, // Renamed from handleAnimationSpeedChange
    setMasterVolume, // For connecting sound manager
    setEffectsVolume, // For connecting sound manager
    loadInitialData, // Action to load data
    isLoadingInitialData, // Loading state
  } = useGameStore();

  // --- Sound Manager Hook ---
  // Initialize sound manager - it reads initial volumes from store via props below
  const soundManager = useSoundManager();

  // --- Sync Zustand volume changes TO Sound Manager ---
  // Effect to update Howler when Zustand state changes (e.g., from settings modal or persistence)
  useEffect(() => {
    soundManager.setMasterVolume(masterVolume);
  }, [masterVolume, soundManager]);

  useEffect(() => {
    soundManager.setEffectsVolume(effectsVolume);
  }, [effectsVolume, soundManager]);

  // --- Sync Sound Manager volume changes TO Zustand ---
  // If useSoundManager had internal ways to change volume (e.g., mute button),
  // you might need an effect to sync back to Zustand, but typically UI drives Zustand first.

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // --- Render Logic ---
  if (isLoadingInitialData || !playerStats) {
    // Display a loading state until initial data is ready
    return (
      <Flex justify="center" align="center" minH="100vh" bg="brand.bgDark">
        {/* TODO: Add a nice Loading Spinner component */}
        <Box color="brand.accent">Loading Adventure...</Box>
      </Flex>
    );
  }

  return (
    <Flex
      direction="column"
      minH="100vh"
      bg="brand.bgDark"
      color="brand.textLight"
    >
      <GameHeader
        playerStats={playerStats} // Pass data slice from store
        onOpenSettings={() => toggleSettings(true)} // Call action
        onOpenInventory={() => toggleInventory(true)} // Call action
      />

      <Box
        as="main"
        flex="1"
        p={4}
        display="flex"
        flexDirection="column"
        overflow="hidden"
      >
        {/* GamePage will access store directly via useGameStore() hook */}
        {children}
      </Box>

      <GameFooter
        onCommandSubmit={sendCommand} // Pass action directly
        isProcessingCommand={isProcessingCommand} // Pass state slice
      />

      {/* Render Modals - Pass state/actions from store */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => toggleSettings(false)}
        // Pass state for display
        masterVolume={masterVolume}
        effectsVolume={effectsVolume}
        animationSpeed={animationSpeed}
        // Pass actions to handle changes
        onMasterVolumeChange={setMasterVolume} // This will update Zustand state
        onEffectsVolumeChange={setEffectsVolume} // This will update Zustand state
        onAnimationSpeedChange={setAnimationSpeed} // This will update Zustand state
      />

      <InventoryModal
        isOpen={isInventoryOpen}
        onClose={() => toggleInventory(false)}
        items={inventory} // Pass state slice
        // Pass actions directly
        onUseItem={useItem}
        onEquipItem={equipItem}
        onDropItem={dropItem}
      />
    </Flex>
  );
}
