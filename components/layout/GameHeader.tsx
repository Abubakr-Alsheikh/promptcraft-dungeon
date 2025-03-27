import {
  Flex,
  Heading,
  Box,
  Spacer,
  IconButton,
  HStack,
  Tooltip,
} from "@chakra-ui/react";
import { GiCog, GiBackpack } from "react-icons/gi";
import { PlayerStats, PlayerStatsData } from "@/components/game/PlayerStats";

interface GameHeaderProps {
  playerStats: PlayerStatsData | null;
  onOpenSettings: () => void;
  onOpenInventory: () => void;
}

export function GameHeader({
  playerStats,
  onOpenSettings,
  onOpenInventory,
}: GameHeaderProps) {
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
        PromptCraft: Dungeon Delver
      </Heading>
      <Spacer />
      <Box flexShrink={0} mx={4}>
        {" "}
        {/* Prevent player stats from causing wrap too early */}
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
            onClick={onOpenInventory}
          />
        </Tooltip>
        <Tooltip label="Settings" placement="bottom" hasArrow>
          <IconButton
            aria-label="Game Settings"
            icon={<GiCog />}
            variant="ghost"
            color="gray.400"
            _hover={{ color: "brand.accent", bg: "gray.700" }}
            onClick={onOpenSettings}
          />
        </Tooltip>
      </HStack>
    </Flex>
  );
}
