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

  // Map rarity to Chakra color scheme defined in theme.ts
  const rarityColorScheme =
    (item.rarity as keyof typeof theme.colors.rarity) || "gray";

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
        borderColor={theme.colors.rarity[rarityColorScheme] || "gray.600"}
        _hover={{ bg: "whiteAlpha.200", shadow: "md" }}
        w="full" // Take full width in grid/wrap
      >
        <VStack align="stretch" spacing={2}>
          <HStack justify="space-between">
            {/* Icon/Image */}
            <Box boxSize="40px" mr={3} flexShrink={0}>
              {item.icon ? (
                // Example: Using react-icons based on name (needs mapping)
                // Or use <Image src={item.icon} alt={item.name} /> for image paths
                <Icon
                  as={GiPerspectiveDiceSixFacesRandom}
                  boxSize="full"
                  color="gray.400"
                /> // Placeholder
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
                colorScheme={rarityColorScheme}
                variant="solid"
                fontSize="xs"
                textTransform="capitalize"
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
              <Spacer /> {/* Push buttons to the right */}
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
