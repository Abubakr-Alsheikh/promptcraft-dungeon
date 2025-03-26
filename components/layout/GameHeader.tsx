import {
  Flex,
  Heading,
  Box,
  Spacer,
  IconButton,
  useDisclosure,
  Tooltip,
} from "@chakra-ui/react";
import { GiCog } from "react-icons/gi"; // Settings icon
import { PlayerStats, PlayerStatsData } from "@/components/game/PlayerStats";
// import SettingsModal from './SettingsModal'; // Placeholder for a settings modal

interface GameHeaderProps {
  playerStats: PlayerStatsData; // Pass player stats data here
}

export function GameHeader({ playerStats }: GameHeaderProps) {
  const { isOpen, onOpen, onClose } = useDisclosure(); // For settings modal

  return (
    <>
      <Flex
        as="header"
        align="center"
        p={3}
        bg="brand.bgDark" // Use dark background from theme
        borderBottomWidth={1}
        borderColor="brand.primary" // Accent border
        wrap="wrap" // Allow wrapping on smaller screens
      >
        <Heading as="h1" size="md" color="brand.accent" fontFamily="heading">
          PromptCraft: Dungeon Delver
        </Heading>
        <Spacer />
        <Box mx={4}>
          {" "}
          {/* Add margin for spacing */}
          <PlayerStats stats={playerStats} />
        </Box>
        <Tooltip label="Settings" placement="bottom" hasArrow>
          <IconButton
            aria-label="Game Settings"
            icon={<GiCog />}
            variant="ghost"
            color="gray.400"
            _hover={{ color: "brand.accent", bg: "gray.700" }}
            onClick={onOpen} // Open settings modal
          />
        </Tooltip>
      </Flex>
      {/* <SettingsModal isOpen={isOpen} onClose={onClose} /> */}
    </>
  );
}
