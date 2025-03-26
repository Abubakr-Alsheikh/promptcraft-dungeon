import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  Wrap, // Use Wrap for responsive grid-like layout
  WrapItem,
  Text,
  Center,
} from "@chakra-ui/react";
import { ItemCard } from "./ItemCard"; // Import Item type and ItemCard
import { Item } from "@/types/game";

interface InventoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  items: Item[];
  onUseItem?: (itemId: string) => void;
  onEquipItem?: (itemId: string) => void;
  onDropItem?: (itemId: string) => void;
}

export function InventoryModal({
  isOpen,
  onClose,
  items,
  onUseItem,
  onEquipItem,
  onDropItem,
}: InventoryModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" scrollBehavior="inside">
      <ModalOverlay bg="blackAlpha.700" backdropFilter="blur(5px)" />
      <ModalContent
        bg="brand.bgDark"
        color="brand.textLight"
        borderWidth={1}
        borderColor="brand.primary"
      >
        <ModalHeader fontFamily="heading" color="brand.accent">
          Inventory
        </ModalHeader>
        <ModalCloseButton _hover={{ bg: "brand.secondary" }} />
        <ModalBody pb={6}>
          {items.length === 0 ? (
            <Center h="100px">
              <Text color="gray.500" fontStyle="italic">
                Your backpack is empty.
              </Text>
            </Center>
          ) : (
            <Wrap spacing={4} justify="center">
              {items.map((item) => (
                <WrapItem
                  key={item.id}
                  w={{
                    base: "100%",
                    sm: "calc(50% - 0.5rem)",
                    md: "calc(33.33% - 1rem)",
                  }}
                >
                  <ItemCard
                    item={item}
                    onUse={onUseItem}
                    onEquip={onEquipItem}
                    onDrop={onDropItem}
                  />
                </WrapItem>
              ))}
            </Wrap>
          )}
        </ModalBody>

        <ModalFooter borderTopWidth={1} borderColor="brand.primary">
          <Button variant="outline" colorScheme="gray" mr={3} onClick={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
