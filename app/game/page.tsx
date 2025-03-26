"use client";

import { VStack, Box } from "@chakra-ui/react";
import { useState } from "react";
import { DungeonView } from "@/components/game/DungeonView";
import { EventLog, LogEntry } from "@/components/game/EventLog";

export default function GamePage() {
  // --- Placeholder State (to be replaced by Zustand/Context) ---
  const [description, setDescription] = useState(
    "You stand at the entrance of a dark, moss-covered cave.\nA cool breeze carries the scent of damp earth and something ancient and metallic.\nThe only way forward is deeper into the darkness."
  );
  const [isLoadingDescription, setIsLoadingDescription] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([
    // Example logs if using EventLog
    { id: 1, text: "Game started.", type: "system" },
    { id: 2, text: "> look around", type: "player" },
    { id: 3, text: "You are at a cave entrance.", type: "narration" },
  ]);
  // --- End Placeholder State ---

  // TODO: Fetch initial description and update based on game events/API responses

  return (
    // Use VStack to stack DungeonView and potentially EventLog
    <VStack spacing={4} align="stretch" flex="1" overflow="hidden">
      {" "}
      {/* Prevent layout shift */}
      {/* Dungeon View takes up most space */}
      <DungeonView
        description={description}
        isLoading={isLoadingDescription}
        animate={true} // Enable animation
      />
      {/* Optional Event Log */}
      <Box>
        <EventLog logs={logs} />
      </Box>
    </VStack>
  );
}
