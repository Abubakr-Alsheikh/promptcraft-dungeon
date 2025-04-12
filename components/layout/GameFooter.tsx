import { Box, VStack, Wrap, WrapItem, Text } from "@chakra-ui/react";
import { PlayerInput } from "@/components/game/PlayerInput";
import { ActionButton } from "@/components/ui/ActionButton";
interface GameFooterProps {
  onCommandSubmit: (command: string) => void;
  isProcessingCommand: boolean;
  suggestedActions: string[] | null;
}

export function GameFooter({
  onCommandSubmit,
  isProcessingCommand,
  suggestedActions,
}: GameFooterProps) {
  const handleSuggestionClick = (suggestion: string) => {
    if (!isProcessingCommand) {
      onCommandSubmit(suggestion);
    }
  };

  return (
    <Box
      as="footer"
      p={4}
      bg="brand.bg"
      borderTopWidth={1}
      borderColor="brand.border"
    >
      <VStack spacing={4} align="stretch">
        {/* Suggested Actions Area */}
        {suggestedActions && suggestedActions.length > 0 && (
          <Box>
            <Text fontSize="sm" color="brand.text" mb={2} textAlign="center">
              Suggestions:
            </Text>
            {/* Use Wrap for responsiveness */}
            <Wrap spacing={2} justify="center">
              {suggestedActions.map((suggestion) => (
                <WrapItem key={suggestion}>
                  {/* Use ActionButton or simpler Button */}
                  <ActionButton
                    label={suggestion}
                    onClickAction={() => handleSuggestionClick(suggestion)}
                    isDisabled={isProcessingCommand}
                    size="sm" // Make buttons slightly smaller
                    variant="outline" // Different visual style for suggestions
                    colorScheme="teal" // Use theme color
                  />
                </WrapItem>
              ))}
            </Wrap>
          </Box>
        )}

        {/* Input remains the same */}
        <PlayerInput
          onSubmitCommand={onCommandSubmit}
          isLoading={isProcessingCommand}
          focusInput={true}
        />
      </VStack>
    </Box>
  );
}
