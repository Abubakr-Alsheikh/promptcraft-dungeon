"use client";

import { useState } from "react";
import { useRouter } from "next/navigation"; // Use next/navigation
import {
  Heading,
  Text,
  Button,
  VStack,
  Container,
  Input,
  FormControl,
  FormLabel,
  Select,
  Spinner,
} from "@chakra-ui/react";
import { useGameStore } from "@/store/gameStore"; // Import the store

export default function HomePage() {
  const router = useRouter();
  const { startGame, isStartingGame, resetGameState } = useGameStore(); // Get actions/state

  const [playerName, setPlayerName] = useState("");
  const [difficulty, setDifficulty] = useState("medium");

  const handleStartGame = async () => {
    // Reset state *before* doing anything else when starting a new game
    console.log("Resetting game state before starting new game...");
    resetGameState();

    // Now proceed with the API call and navigation logic
    console.log("Game state reset, attempting to start game via API...");
    const success = await startGame(playerName, difficulty);
    if (success) {
      console.log("Start game successful, navigating...");
      router.push("/game"); // Navigate to game page on success
    } else {
      // Error toast is handled within the startGame action via useNotificationStore
      // You could add additional UI feedback here if needed
      console.log("Start game failed, staying on page.");
    }
  };

  return (
    <Container centerContent maxW="container.md" py={10} minH="80vh">
      <VStack spacing={6} textAlign="center" w="100%">
        <Heading as="h1" size="2xl" fontFamily="heading" color="brand.accent">
          PromptCraft: Dungeon Delver
        </Heading>
        <Text fontSize="lg" color="brand.text" maxW="lg">
          Forge your legend in a world shaped by words. Enter your name, choose
          your fate, and begin your AI-powered text adventure.
        </Text>

        <VStack
          spacing={4}
          as="form"
          w="sm"
          onSubmit={(e) => {
            e.preventDefault();
            handleStartGame();
          }}
        >
          <FormControl id="player-name">
            <FormLabel color="brand.text">Enter Your Name:</FormLabel>
            <Input
              placeholder="Adventurer"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              borderColor="brand.text"
              focusBorderColor="brand.accent"
              _hover={{ borderColor: "brand.textMedium" }}
              bg="brand.bg"
              color="brand.textDark"
              isDisabled={isStartingGame}
            />
          </FormControl>

          <FormControl id="difficulty">
            <FormLabel color="brand.text">Choose Difficulty:</FormLabel>
            <Select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              borderColor="brand.textDark"
              focusBorderColor="brand.accent"
              _hover={{ borderColor: "brand.textMedium" }}
              bg="brand.bg"
              color="brand.textDark" // Ensure text is visible
              iconColor="brand.textMedium"
              isDisabled={isStartingGame}
            >
              <option
                style={{ backgroundColor: "#333", color: "#eee" }}
                value="easy"
              >
                Easy
              </option>
              <option
                style={{ backgroundColor: "#333", color: "#eee" }}
                value="medium"
              >
                Medium
              </option>
              <option
                style={{ backgroundColor: "#333", color: "#eee" }}
                value="hard"
              >
                Hard
              </option>
            </Select>
          </FormControl>

          <Button
            mt={4}
            colorScheme="yellow"
            variant="solid"
            size="lg"
            bg="brand.accent"
            color="brand.bgDark"
            _hover={{ bg: "yellow.400" }}
            onClick={handleStartGame}
            isLoading={isStartingGame} // Show loading state on button
            spinner={<Spinner size="sm" />}
            loadingText="Generating World..."
            isDisabled={isStartingGame}
            type="submit" // Allow form submission via Enter key
          >
            Begin Your Adventure!
          </Button>
        </VStack>
      </VStack>
    </Container>
  );
}
