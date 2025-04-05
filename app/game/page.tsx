"use client";

import { VStack, Box, Heading, Divider } from "@chakra-ui/react"; // Import Heading, Divider
import { DungeonView } from "@/components/game/DungeonView";
import { EventLog } from "@/components/game/EventLog";
import { useGameStore } from "@/store/gameStore"; // Import the store hook

export default function GamePage() {
  // --- Get necessary state slices from Zustand ---
  const {
    description, // Persistent room description
    roomTitle, // NEW: Get room title
    isProcessingCommand,
    animationSpeed,
    logs, // Logs now contain action result messages
  } = useGameStore();

  return (
    // Use VStack to stack DungeonView and EventLog
    <VStack spacing={4} align="stretch" flex="1" overflow="hidden">
      {/* Optional: Display Room Title */}
      {roomTitle && (
        <Heading
          as="h2"
          size="lg"
          textAlign="center"
          fontFamily="heading"
          color="brand.accent"
          mt={2} // Add some top margin
          noOfLines={1} // Prevent wrapping issues
        >
          {roomTitle}
        </Heading>
      )}

      {/* Dungeon View shows the persistent room description */}
      <DungeonView
        description={description}
        isLoading={isProcessingCommand && !description} // Show loading only if description is also empty maybe?
        speed={animationSpeed}
        animate={animationSpeed > 0}
      />

      <Divider borderColor="gray.600" />

      {/* Event Log shows player commands, system messages, and action results */}
      <Box>
        <EventLog logs={logs} />
      </Box>
    </VStack>
  );
}
