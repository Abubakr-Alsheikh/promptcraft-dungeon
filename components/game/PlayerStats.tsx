import { HStack, Text, Box, Icon, Tooltip } from "@chakra-ui/react";
import { GiHeartBottle, GiCoins, GiStarSwirl } from "react-icons/gi"; // Example icons
import { ProgressBar } from "@/components/feedback/ProgressBar";

// Define a type for player stats (will come from state management)
export interface PlayerStatsData {
  currentHp: number;
  maxHp: number;
  gold: number;
  xp?: number;
  maxXp?: number;
  level?: number;
}

interface PlayerStatsProps {
  stats: PlayerStatsData;
}

export function PlayerStats({ stats }: PlayerStatsProps) {
  return (
    <HStack spacing={{ base: 3, md: 6 }} align="center" wrap="wrap">
      <Tooltip
        label={`Health: ${stats.currentHp} / ${stats.maxHp}`}
        placement="bottom"
        hasArrow
      >
        <HStack>
          <Icon as={GiHeartBottle} color="red.400" boxSize={5} />
          <Box w={{ base: "60px", md: "100px" }}>
            <ProgressBar
              value={stats.currentHp}
              max={stats.maxHp}
              colorScheme="green" // ProgressBar handles color logic internally
              showValue={false} // Keep it cleaner in the header
              aria-label={`Health ${stats.currentHp} of ${stats.maxHp}`}
            />
          </Box>
          <Text
            fontSize="sm"
            fontWeight="bold"
          >{`${stats.currentHp}/${stats.maxHp}`}</Text>
        </HStack>
      </Tooltip>

      <Tooltip label={`Gold: ${stats.gold}`} placement="bottom" hasArrow>
        <HStack>
          <Icon as={GiCoins} color="brand.accent" boxSize={5} />
          <Text fontSize="md" fontWeight="bold" color="brand.accent">
            {stats.gold}
          </Text>
        </HStack>
      </Tooltip>

      {/* XP Bar */}
      {stats.xp !== undefined && stats.maxXp !== undefined && (
        <Tooltip
          label={`Experience: ${stats.xp} / ${stats.maxXp}`}
          placement="bottom"
          hasArrow
        >
          <HStack>
            <Icon as={GiStarSwirl} color="blue.400" boxSize={5} />
            <Box w={{ base: "60px", md: "100px" }}>
              <ProgressBar
                value={stats.xp}
                max={stats.maxXp}
                colorScheme="blue"
                showValue={false}
                aria-label={`Experience ${stats.xp} of ${stats.maxXp}`}
              />
            </Box>
            {/* Optionally show Level */}
            {stats.level !== undefined && (
              <Text fontSize="sm" fontWeight="bold">
                Lvl {stats.level}
              </Text>
            )}
          </HStack>
        </Tooltip>
      )}
    </HStack>
  );
}
