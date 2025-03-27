import { Box, Text } from "@chakra-ui/react";
import { AnimatedText } from "@/components/feedback/AnimatedText";

interface DungeonViewProps {
  description: string;
  isLoading?: boolean;
  speed?: number;
  animate?: boolean;
}

export function DungeonView({
  description,
  isLoading = false,
  speed = 50,
  animate = true,
}: DungeonViewProps) {
  // Use a key based on the description to force re-render/re-animate AnimatedText
  const animationKey = description;

  return (
    <Box
      flex="1"
      p={4}
      borderWidth={1}
      borderColor="gray.600"
      borderRadius="md"
      overflowY="auto" // Make it scrollable if content exceeds height
      bg="rgba(0, 0, 0, 0.2)" // Slightly darker background for contrast
      sx={{
        // Smooth scrolling
        "&::-webkit-scrollbar": { width: "8px" },
        "&::-webkit-scrollbar-track": { background: "gray.700" },
        "&::-webkit-scrollbar-thumb": {
          background: "brand.secondary",
          borderRadius: "4px",
        },
        "&::-webkit-scrollbar-thumb:hover": { background: "brand.primary" },
      }}
    >
      {isLoading ? (
        <Text fontStyle="italic" color="gray.400">
          Loading description...
        </Text>
      ) : animate ? (
        <AnimatedText
          key={animationKey}
          text={description}
          speed={speed}
          fontSize="lg"
          lineHeight="tall"
        />
      ) : (
        <Text fontSize="lg" lineHeight="tall" whiteSpace="pre-wrap">
          {description}
        </Text>
      )}
    </Box>
  );
}
