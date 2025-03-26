import { useState, FormEvent, useRef, useEffect } from "react";
import { Input, Button, HStack, FormControl, Box } from "@chakra-ui/react";
import { GiArrowCluster } from "react-icons/gi";

interface PlayerInputProps {
  onSubmitCommand: (command: string) => void;
  isLoading?: boolean;
  focusInput?: boolean;
}

export function PlayerInput({
  onSubmitCommand,
  isLoading = false,
  focusInput = true,
}: PlayerInputProps) {
  const [inputValue, setInputValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const command = inputValue.trim();
    if (command && !isLoading) {
      onSubmitCommand(command);
      setInputValue(""); // Clear input after submit
    }
  };

  // Focus the input element when the component mounts or focusInput becomes true
  useEffect(() => {
    if (focusInput && inputRef.current) {
      // Use timeout to ensure focus happens after potential re-renders
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 50); // Small delay often helps
      return () => clearTimeout(timer);
    }
  }, [focusInput]);

  return (
    <Box w="full">
      <form onSubmit={handleSubmit}>
        <FormControl id="player-command">
          <HStack>
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="What do you do?"
              isDisabled={isLoading}
              bg="gray.700" // Slightly lighter input background
              borderColor="gray.600"
              _hover={{ borderColor: "brand.secondary" }}
              _focus={{
                borderColor: "brand.primary",
                boxShadow: `0 0 0 1px var(--chakra-colors-brand-primary)`,
              }} // Use theme color for focus
            />
            <Button
              type="submit"
              colorScheme="yellow" // Matches accent
              bg="brand.accent"
              color="brand.bgDark"
              _hover={{ bg: "yellow.400" }}
              isLoading={isLoading}
              isDisabled={!inputValue.trim()} // Disable if input is empty
              px={6}
              rightIcon={<GiArrowCluster />}
            >
              Send
            </Button>
          </HStack>
        </FormControl>
      </form>
    </Box>
  );
}
