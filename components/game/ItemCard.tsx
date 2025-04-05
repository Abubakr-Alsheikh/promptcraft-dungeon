import { Item } from "@/types/game";
import {
  Box,
  Text,
  VStack,
  HStack,
  Tooltip,
  Badge,
  Button,
  Icon,
  Spacer,
  useTheme,
} from "@chakra-ui/react";
import { GiPerspectiveDiceSixFacesRandom } from "react-icons/gi"; // Default icon

interface ItemCardProps {
  item: Item;
  onUse?: (itemId: string) => void;
  onEquip?: (itemId: string) => void;
  onDrop?: (itemId: string) => void;
}

export function ItemCard({ item, onUse, onEquip, onDrop }: ItemCardProps) {
  const theme = useTheme();

  // Determine the Rarity Color directly from the theme
  const rarityColor =
    theme.colors.rarity?.[item.rarity as keyof typeof theme.colors.rarity] ?? // Access theme using rarity name
    theme.colors.gray?.[400] ?? // Sensible fallback using theme's gray
    "#A0AEC0"; // Ultimate fallback color value if gray.400 also missing

  // Use this theme-defined color for both the border and the badge background
  const borderColor = rarityColor;
  const badgeBgColor = rarityColor;

  const badgeTextColor = "white";

  const handleUse = () => onUse && onUse(item.id);
  const handleEquip = () => onEquip && onEquip(item.id);
  const handleDrop = () => onDrop && onDrop(item.id);

  return (
    <Tooltip label={item.description} placement="top" hasArrow openDelay={500}>
      <Box
        borderWidth={1}
        borderRadius="md"
        p={3}
        bg="whiteAlpha.100"
        borderColor={borderColor as string}
        _hover={{ bg: "whiteAlpha.200", shadow: "md" }}
        w="full"
      >
        <VStack align="stretch" spacing={2}>
          <HStack justify="space-between">
            {/* Icon/Image */}
            <Box boxSize="40px" mr={3} flexShrink={0}>
              {item.icon ? (
                <Icon
                  as={GiPerspectiveDiceSixFacesRandom}
                  boxSize="full"
                  color="gray.400"
                />
              ) : (
                <Icon
                  as={GiPerspectiveDiceSixFacesRandom}
                  boxSize="full"
                  color="gray.400"
                />
              )}
            </Box>

            {/* Name and Quantity */}
            <VStack align="start" spacing={0} flex="1">
              <Text fontWeight="bold" fontSize="md" noOfLines={1}>
                {item.name}
              </Text>
              <Badge
                bg={badgeBgColor as string}
                color={badgeTextColor}
                fontSize="xs"
                textTransform="capitalize"
                px={2}
                borderRadius="sm"
              >
                {item.rarity}
              </Badge>
            </VStack>

            {item.quantity > 1 && (
              <Text fontSize="lg" fontWeight="bold" color="gray.300">
                x{item.quantity}
              </Text>
            )}
          </HStack>

          {/* Action Buttons */}
          {(item.canUse || item.canEquip || item.canDrop) && (
            <HStack
              spacing={2}
              pt={2}
              borderTopWidth={1}
              borderColor="whiteAlpha.200"
            >
              <Spacer />
              {item.canUse && onUse && (
                <Button
                  size="xs"
                  variant="outline"
                  colorScheme="green"
                  onClick={handleUse}
                >
                  Use
                </Button>
              )}
              {item.canEquip && onEquip && (
                <Button
                  size="xs"
                  variant="outline"
                  colorScheme="blue"
                  onClick={handleEquip}
                >
                  Equip
                </Button>
              )}
              {item.canDrop && onDrop && (
                <Button
                  size="xs"
                  variant="outline"
                  colorScheme="red"
                  onClick={handleDrop}
                >
                  Drop
                </Button>
              )}
            </HStack>
          )}
        </VStack>
      </Box>
    </Tooltip>
  );
}
