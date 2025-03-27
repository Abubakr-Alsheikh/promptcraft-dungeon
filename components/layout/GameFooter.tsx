import { Box, HStack, VStack } from "@chakra-ui/react";
import { PlayerInput } from "@/components/game/PlayerInput";
import { ActionButton } from "@/components/ui/ActionButton";
import { GiBackpack, GiMagnifyingGlass } from "react-icons/gi";

interface GameFooterProps {
  onCommandSubmit: (command: string) => void;
  isProcessingCommand: boolean;
  onLookAction?: () => void;
  onInventoryAction?: () => void;
}

export function GameFooter({
  onCommandSubmit,
  isProcessingCommand,
  onLookAction,
  onInventoryAction,
}: GameFooterProps) {
  return (
    <Box
      as="footer"
      p={4}
      bg="brand.bgDark"
      borderTopWidth={1}
      borderColor="gray.700"
    >
      <VStack spacing={4}>
        {/* Quick Action Buttons */}
        <HStack spacing={3} justify="center">
          <ActionButton
            label="Look Around"
            icon={<GiMagnifyingGlass />}
            onClickAction={onLookAction}
            isDisabled={isProcessingCommand}
          />
          <ActionButton
            label="Inventory"
            icon={<GiBackpack />}
            onClickAction={onInventoryAction}
            isDisabled={isProcessingCommand}
          />
        </HStack>

        <PlayerInput
          onSubmitCommand={onCommandSubmit}
          isLoading={isProcessingCommand}
          focusInput={true} // Keep input focused by default
        />
      </VStack>
    </Box>
  );
}
