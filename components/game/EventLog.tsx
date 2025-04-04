import { LogEntry } from "@/types/game";
import { Box, Text, VStack } from "@chakra-ui/react";
import { useEffect, useRef } from "react";

interface EventLogProps {
  logs: LogEntry[];
  maxEntries?: number;
}

export function EventLog({ logs, maxEntries = 20 }: EventLogProps) {
  const displayedLogs = logs.slice(-maxEntries);
  const logContainerRef = useRef<HTMLDivElement>(null);

  const getLogColor = (type: LogEntry["type"]) => {
    switch (type) {
      case "player":
        return "blue.300";
      case "system":
        return "green.300";
      case "error":
        return "red.300";
      case "narration":
      default:
        return "gray.400";
    }
  };
  const getLogIcon = (type: LogEntry["type"]) => {
    switch (type) {
      case "player":
        return "👤";
      case "system":
        return "🤖";
      case "error":
        return "❌";
      case "narration":
      default:
        return "📜";
    }
  };
  // Effect to scroll to bottom when logs change
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <Box
      h="150px"
      overflowY="auto"
      p={3}
      borderWidth={1}
      borderColor="gray.700"
      borderRadius="md"
      bg="rgba(0, 0, 0, 0.1)"
      fontSize="sm"
      sx={{
        // Custom scrollbar for consistency
        "&::-webkit-scrollbar": { width: "6px" },
        "&::-webkit-scrollbar-track": { background: "gray.800" },
        "&::-webkit-scrollbar-thumb": {
          background: "gray.600",
          borderRadius: "3px",
        },
      }}
    >
      <VStack align="stretch" spacing={1}>
        {displayedLogs.length === 0 && (
          <Text color="gray.500">No events yet...</Text>
        )}
        {displayedLogs.map((log) => (
          <Text
            key={log.id}
            color={getLogColor(log.type)}
            whiteSpace="pre-wrap"
          >
            {/* Optional: Add prefix based on type */}
            {getLogIcon(log.type)}
            {log.type === "player" && "> "}
            {log.text}
          </Text>
        ))}
      </VStack>
    </Box>
  );
}
