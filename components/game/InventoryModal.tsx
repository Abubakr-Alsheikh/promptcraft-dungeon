import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  Wrap,
  WrapItem,
  Text,
  Center,
} from "@chakra-ui/react";
import { ItemCard } from "./ItemCard";
import { useGameStore } from "@/store/gameStore";

export function InventoryModal() {
  const isOpen = useGameStore((state) => state.isInventoryOpen);
  const toggleInventory = useGameStore((state) => state.toggleInventory);
  const items = useGameStore((state) => state.inventory);
  const onUseItem = useGameStore((state) => state.useItem);
  const onEquipItem = useGameStore((state) => state.equipItem);
  const onDropItem = useGameStore((state) => state.dropItem);

  const handleClose = () => toggleInventory(false);

  if (!isOpen) {
    return null;
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      size="xl"
      scrollBehavior="inside"
      isCentered
    >
      <ModalOverlay bg="blackAlpha.700" backdropFilter="blur(5px)" />
      <ModalContent
        bg="brand.bgDark"
        color="brand.text"
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
          <Button
            variant="outline"
            colorScheme="gray"
            mr={3}
            onClick={handleClose}
          >
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
