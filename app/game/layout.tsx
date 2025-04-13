"use client";

import { Box, Flex, Spinner, Text } from "@chakra-ui/react";
import { ReactNode, useEffect } from "react";
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
  const gameId = useGameStore((state) => state.gameId);
  const playerStatsExist = useGameStore((state) => !!state.playerStats); // Just check existence
  const isStartingGame = useGameStore((state) => state.isStartingGame);

  const masterVolume = useGameStore((state) => state.masterVolume);
  const effectsVolume = useGameStore((state) => state.effectsVolume);
  const lastSoundEffect = useGameStore((state) => state.lastSoundEffect);
  const clearLastSoundEffect = useGameStore(
    (state) => state.clearLastSoundEffect
  );

  const soundManager = useSoundManager();

  // --- Redirect Logic (remains the same) ---
  useEffect(() => {
    if (!isStartingGame && (!gameId || !playerStatsExist)) {
      console.log(
        "GameLayout: Missing gameId or playerStats, redirecting to home. gameId:",
        gameId,
        "isStartingGame:",
        isStartingGame
      );
      router.replace("/");
    }
  }, [gameId, playerStatsExist, isStartingGame, router]);

  // --- Volume Sync Effects ---
  useEffect(() => {
    if (soundManager.isInitialized) {
      soundManager.setMasterVolume(masterVolume);
    }
  }, [masterVolume, soundManager]);

  useEffect(() => {
    if (soundManager.isInitialized) {
      soundManager.setEffectsVolume(effectsVolume);
    }
  }, [effectsVolume, soundManager]);

  // --- Sound Effect Player (remains the same) ---
  useEffect(() => {
    if (lastSoundEffect && soundManager.isInitialized) {
      console.log(
        `GameLayout: Playing sound effect from state: ${lastSoundEffect}`
      );
      soundManager.playSound(lastSoundEffect, true);
      clearLastSoundEffect();
    }
  }, [lastSoundEffect, soundManager, clearLastSoundEffect]);

  // --- Loading States ---
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
        <Text color="brand.text" fontSize="lg">
          Generating your adventure...
        </Text>
      </Flex>
    );
  }
  // Use playerStatsExist for the check
  if (!gameId || !playerStatsExist) {
    return (
      <Flex
        justify="center"
        align="center"
        minH="100vh"
        bg="brand.bg"
        direction="column"
        gap={4}
      >
        <Spinner size="xl" color="brand.accent" thickness="4px" />
        <Text color="brand.text">Loading game data...</Text>
      </Flex>
    );
  }

  // --- Render Full Game UI ---
  return (
    <Flex direction="column" minH="100vh" bg="brand.bg" color="brand.text">
      <GameHeader />
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
      <GameFooter />
      <SettingsModal />
      <InventoryModal />
    </Flex>
  );
}
