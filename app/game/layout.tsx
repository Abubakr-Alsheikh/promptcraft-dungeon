"use client";

import { Box, Flex } from "@chakra-ui/react";
import { ReactNode, useState } from "react";
import { GameHeader } from "@/components/layout/GameHeader";
import { GameFooter } from "@/components/layout/GameFooter";
import { PlayerStatsData } from "@/components/game/PlayerStats";

interface GameLayoutProps {
  children: ReactNode;
}

export default function GameLayout({ children }: GameLayoutProps) {
  // --- Placeholder State (to be replaced by Zustand/Context) ---
  const [isProcessing, setIsProcessing] = useState(false);
  const [playerStats, setPlayerStats] = useState<PlayerStatsData>({
    currentHp: 85,
    maxHp: 100,
    gold: 120,
    xp: 150,
    maxXp: 500,
    level: 3,
  });

  const handleCommandSubmit = (command: string) => {
    console.log("Command submitted:", command);
    setIsProcessing(true);
    // TODO: Send command to backend API
    // Simulate API call
    setTimeout(() => {
      // TODO: Update state based on API response (description, stats, logs)
      setPlayerStats((prev) => ({
        ...prev,
        gold: prev.gold + 10,
        currentHp: Math.max(0, prev.currentHp - 5),
      })); // Example update
      setIsProcessing(false);
    }, 1500);
  };
  // --- End Placeholder State ---

  return (
    <Flex
      direction="column"
      minH="100vh"
      bg="brand.bgDark"
      color="brand.textLight"
    >
      <GameHeader playerStats={playerStats} />
      <Box
        as="main"
        flex="1"
        p={4}
        display="flex"
        flexDirection="column"
        overflow="hidden"
      >
        {" "}
        {/* Prevent layout shift */}
        {/* Pass state down - replace with context/store access later */}
        {children}
      </Box>
      <GameFooter
        onCommandSubmit={handleCommandSubmit}
        isProcessingCommand={isProcessing}
      />
    </Flex>
  );
}
