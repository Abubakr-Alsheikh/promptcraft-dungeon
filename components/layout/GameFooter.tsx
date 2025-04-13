import { Box, VStack, Wrap, WrapItem, Text } from "@chakra-ui/react";
import { PlayerInput } from "@/components/game/PlayerInput";
import { ActionButton } from "@/components/ui/ActionButton";
import { useGameStore } from "@/store/gameStore";

export function GameFooter() {
  const sendCommand = useGameStore((state) => state.sendCommand);
  const isProcessingCommand = useGameStore(
    (state) => state.isProcessingCommand
  );
  const suggestedActions = useGameStore((state) => state.suggestedActions);

  const handleSuggestionClick = (suggestion: string) => {
    if (!isProcessingCommand) {
      sendCommand(suggestion);
    }
  };

  return (
    <Box
      as="footer"
      p={4}
      bg="brand.bg"
      borderTopWidth={1}
      borderColor="brand.primary"
    >
      <VStack spacing={4} align="stretch">
        {/* Suggested Actions Area */}
        {suggestedActions && suggestedActions.length > 0 && (
          <Box>
            <Text fontSize="sm" color="brand.text" mb={2} textAlign="center">
              Suggestions:
            </Text>
            <Wrap spacing={2} justify="center">
              {suggestedActions.map((suggestion) => (
                <WrapItem key={suggestion}>
                  <ActionButton
                    label={suggestion}
                    onClickAction={() => handleSuggestionClick(suggestion)}
                    isDisabled={isProcessingCommand} // Use state from store
                    size="sm"
                    variant="outline"
                    colorScheme="teal" // Consider using a brand color? e.g., primary/secondary
                    borderColor="brand.secondary" // Example
                    color="brand.text"
                    _hover={{ bg: "brand.secondary", color: "white" }}
                  />
                </WrapItem>
              ))}
            </Wrap>
          </Box>
        )}

        {/* Player Input Component */}
        <PlayerInput
          onSubmitCommand={sendCommand} // Pass action from store
          isLoading={isProcessingCommand} // Pass state from store
          focusInput={true} // Keep focus logic
        />
      </VStack>
    </Box>
  );
}
