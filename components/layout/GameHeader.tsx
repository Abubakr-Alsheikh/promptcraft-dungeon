import {
  Flex,
  Heading,
  Box,
  Spacer,
  IconButton,
  HStack,
  Tooltip,
  Text,
} from "@chakra-ui/react";
import { GiCog, GiBackpack } from "react-icons/gi";
import { PlayerStats } from "@/components/game/PlayerStats";
import { useGameStore } from "@/store/gameStore";

export function GameHeader() {
  const playerStats = useGameStore((state) => state.playerStats);
  const toggleSettings = useGameStore((state) => state.toggleSettings);
  const toggleInventory = useGameStore((state) => state.toggleInventory);

  if (!playerStats) {
    return null;
  }

  return (
    <Flex
      as="header"
      align="center"
      p={3}
      bg="brand.bgDark"
      borderBottomWidth={1}
      borderColor="brand.primary"
      wrap="wrap"
    >
      <Heading
        as="h1"
        size="md"
        color="brand.accent"
        fontFamily="heading"
        mr={4}
      >
        PromptCraft
        <Text display={{ base: "none", md: "inline" }}>: Dungeon Delver</Text>
      </Heading>
      <Spacer />
      <Box flexShrink={0} mx={{ base: 2, md: 4 }}>
        <PlayerStats stats={playerStats} />
      </Box>
      <HStack spacing={2}>
        <Tooltip label="Inventory" placement="bottom" hasArrow>
          <IconButton
            aria-label="Open Inventory"
            icon={<GiBackpack />}
            variant="ghost"
            color="gray.400"
            _hover={{ color: "brand.accent", bg: "gray.700" }}
            onClick={() => toggleInventory(true)}
          />
        </Tooltip>
        <Tooltip label="Settings" placement="bottom" hasArrow>
          <IconButton
            aria-label="Game Settings"
            icon={<GiCog />}
            variant="ghost"
            color="gray.400"
            _hover={{ color: "brand.accent", bg: "gray.700" }}
            onClick={() => toggleSettings(true)}
          />
        </Tooltip>
      </HStack>
    </Flex>
  );
}
