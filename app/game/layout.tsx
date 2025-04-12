"use client";

import { Box, Flex, Spinner, Text } from "@chakra-ui/react";
import { ReactNode, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
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
  const router = useRouter();
  const {
    gameId,
    playerStats,
    inventory,
    isProcessingCommand,
    isStartingGame,
    isInventoryOpen,
    isSettingsOpen,
    animationSpeed,
    masterVolume,
    effectsVolume,
    lastSoundEffect,
    suggestedActions,
    // Actions
    sendCommand,
    useItem,
    equipItem,
    dropItem,
    toggleInventory,
    toggleSettings,
    setAnimationSpeed,
    setMasterVolume,
    setEffectsVolume,
    clearLastSoundEffect,
  } = useGameStore();
  console.log(suggestedActions);
  const soundManager = useSoundManager();

  // --- Redirect Logic (remains the same) ---
  useEffect(() => {
    if (!isStartingGame && (!gameId || !playerStats)) {
      console.log(
        "GameLayout: Missing gameId or playerStats, redirecting to home. gameId:",
        gameId,
        "isStartingGame:",
        isStartingGame
      );
      router.replace("/");
    } else {
      // console.log("GameLayout: Guard passed. gameId:", gameId, "isStartingGame:", isStartingGame);
    }
  }, [gameId, playerStats, isStartingGame, router]);

  // --- Volume Sync Effects (remain the same) ---
  useEffect(() => {
    soundManager.setMasterVolume(masterVolume);
  }, [masterVolume, soundManager]);

  useEffect(() => {
    soundManager.setEffectsVolume(effectsVolume);
  }, [effectsVolume, soundManager]);

  // --- Inventory Toggle Callback (still needed for HEADER) ---
  const handleInventoryToggle = useCallback(() => {
    toggleInventory(true); // Explicitly open
  }, [toggleInventory]);

  // --- Sound Effect Player (remains the same) ---
  useEffect(() => {
    if (lastSoundEffect && soundManager.isInitialized) {
      console.log(`Playing sound effect from state: ${lastSoundEffect}`);
      soundManager.playSound(lastSoundEffect, true);
      clearLastSoundEffect();
    }
  }, [lastSoundEffect, soundManager, clearLastSoundEffect]);

  // --- Loading States (remain the same) ---
  if (isStartingGame) {
    return (
      <Flex
        justify="center"
        align="center"
        minH="100vh"
        bg="brand.bgDark"
        direction="column"
        gap={4}
      >
        <Spinner size="xl" color="brand.accent" thickness="4px" />
        <Text color="brand.textLight" fontSize="lg">
          Generating your adventure...
        </Text>
      </Flex>
    );
  }
  if (!gameId || !playerStats) {
    return (
      <Flex
        justify="center"
        align="center"
        minH="100vh"
        bg="brand.bgDark"
        direction="column"
        gap={4}
      >
        <Spinner size="xl" color="brand.accent" thickness="4px" />
        <Text color="brand.textLight">Loading game data...</Text>
      </Flex>
    );
  }

  // --- Render Full Game UI ---
  return (
    <Flex direction="column" minH="100vh" bg="brand.bgDark" color="brand.text">
      {/* Header still needs its inventory toggle */}
      <GameHeader
        playerStats={playerStats}
        onOpenSettings={() => toggleSettings(true)}
        onOpenInventory={handleInventoryToggle}
      />

      <Box
        as="main"
        flex="1"
        p={4}
        display="flex"
        flexDirection="column"
        overflow="hidden"
      >
        {children}
      </Box>

      {/* Pass suggestedActions and sendCommand to Footer */}
      <GameFooter
        onCommandSubmit={sendCommand}
        isProcessingCommand={isProcessingCommand}
        suggestedActions={suggestedActions} // <-- Pass down
      />

      {/* Modals remain the same */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => toggleSettings(false)}
        masterVolume={masterVolume}
        effectsVolume={effectsVolume}
        animationSpeed={animationSpeed}
        onMasterVolumeChange={setMasterVolume}
        onEffectsVolumeChange={setEffectsVolume}
        onAnimationSpeedChange={setAnimationSpeed}
      />

      <InventoryModal
        isOpen={isInventoryOpen}
        onClose={() => toggleInventory(false)}
        items={inventory}
        onUseItem={useItem}
        onEquipItem={equipItem}
        onDropItem={dropItem}
      />
    </Flex>
  );
}
