import { useState, useEffect } from "react"; // Import useEffect
import {
  Container,
  Text,
  Input,
  Button,
  VStack,
  Heading,
  Spinner,
  HStack,
} from "@chakra-ui/react"; // Add HStack
import { generateText } from "../utils/api";

export default function Home() {
  const [roomDescription, setRoomDescription] = useState(""); // Initialize as empty
  const [playerInput, setPlayerInput] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [playerHealth, setPlayerHealth] = useState(10); // Add player health
  const [playerLocation, setPlayerLocation] = useState("start"); // Add player location

  // Use useEffect to fetch the initial room description when the component mounts
  useEffect(() => {
    const startGame = async () => {
      setIsLoading(true);
      try {
        const initialDescription = await generateText("Start game"); // Special start prompt
        setRoomDescription(initialDescription);
        setMessages([initialDescription]);
      } catch (error) {
        setMessages([String(error)]);
      } finally {
        setIsLoading(false);
      }
    };
    startGame();
  }, []); // Empty dependency array ensures this runs only once on mount

  const handleSubmit = async () => {
    if (!playerInput.trim()) return;

    setIsLoading(true);
    try {
      const newDescription = await generateText(
        playerInput,
        null,
        roomDescription,
        playerInput
      ); //Pass parameters
      setRoomDescription(newDescription);
      setMessages([...messages, `> ${playerInput}`, newDescription]);
      setPlayerInput("");
    } catch (error) {
      setMessages([...messages, `> ${playerInput}`, String(error)]);
      setPlayerInput("");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxW="container.md" py={4}>
      <Heading as="h1" size="xl" mb={4}>
        PromptCraft: Dungeon Delver
      </Heading>

      <VStack spacing={4} align="stretch">
        <HStack>
          <Text fontSize="lg" fontWeight="bold">
            Health: {playerHealth}
          </Text>
          <Text fontSize="lg">Location: {playerLocation}</Text>
        </HStack>

        <Text fontSize="lg">{roomDescription}</Text>

        {messages.map((msg, index) => (
          <Text key={index} color={msg.startsWith(">") ? "gray.400" : "white"}>
            {msg}
          </Text>
        ))}

        <Input
          value={playerInput}
          onChange={(e) => setPlayerInput(e.target.value)}
          placeholder="Enter your command (e.g., explore north)"
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          isDisabled={isLoading}
        />
        <Button
          colorScheme="blue"
          onClick={handleSubmit}
          isLoading={isLoading}
          loadingText="Generating..."
        >
          Submit
        </Button>
      </VStack>
    </Container>
  );
}
