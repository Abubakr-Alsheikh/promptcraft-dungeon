"use client";

import { VStack, Box } from "@chakra-ui/react";
import { DungeonView } from "@/components/game/DungeonView";
import { EventLog } from "@/components/game/EventLog"; // Assuming you want the log now
import { useGameStore } from "@/store/gameStore"; // Import the store hook

export default function GamePage() {
  // --- Get necessary state slices from Zustand ---
  const {
    description,
    isProcessingCommand, // Can use this instead of a separate isLoadingDescription
    animationSpeed,
    logs, // Get logs state
  } = useGameStore();

  return (
    // Use VStack to stack DungeonView and EventLog
    <VStack spacing={4} align="stretch" flex="1" overflow="hidden">
      {/* Dungeon View takes up most space */}
      <DungeonView
        description={description}
        isLoading={isProcessingCommand} // Use the command processing flag for loading indicator
        speed={animationSpeed}
        animate={animationSpeed > 0}
      />

      {/* Optional Event Log */}
      <Box>
        <EventLog logs={logs} />
      </Box>
    </VStack>
  );
}
