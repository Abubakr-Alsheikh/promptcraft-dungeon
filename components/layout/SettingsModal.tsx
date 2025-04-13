import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  FormControl,
  FormLabel,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  HStack,
  Text,
  useColorMode,
  Select,
  Switch,
} from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { useGameStore } from "@/store/gameStore";

export function SettingsModal() {
  const isOpen = useGameStore((state) => state.isSettingsOpen);
  const toggleSettings = useGameStore((state) => state.toggleSettings);
  const initialMasterVolume = useGameStore((state) => state.masterVolume);
  const setMasterVolume = useGameStore((state) => state.setMasterVolume);
  const initialEffectsVolume = useGameStore((state) => state.effectsVolume);
  const setEffectsVolume = useGameStore((state) => state.setEffectsVolume);
  const initialAnimationSpeed = useGameStore((state) => state.animationSpeed);
  const setAnimationSpeed = useGameStore((state) => state.setAnimationSpeed);

  const { colorMode, toggleColorMode } = useColorMode();

  // --- Local state for smoother slider interaction ---
  const [localMasterVolume, setLocalMasterVolume] =
    useState(initialMasterVolume);
  const [localEffectsVolume, setLocalEffectsVolume] =
    useState(initialEffectsVolume);
  const [localAnimationSpeed, setLocalAnimationSpeed] = useState(
    initialAnimationSpeed
  );

  // Sync local state if global state changes externally (e.g., hydration)
  useEffect(() => {
    setLocalMasterVolume(initialMasterVolume);
  }, [initialMasterVolume]);

  useEffect(() => {
    setLocalEffectsVolume(initialEffectsVolume);
  }, [initialEffectsVolume]);

  useEffect(() => {
    setLocalAnimationSpeed(initialAnimationSpeed);
  }, [initialAnimationSpeed]);

  const handleMasterVolumeSliderChangeEnd = (value: number) => {
    setMasterVolume(value);
  };
  const handleEffectsVolumeSliderChangeEnd = (value: number) => {
    setEffectsVolume(value);
  };
  const handleAnimationSpeedChange = (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const speed = parseInt(event.target.value, 10);
    setLocalAnimationSpeed(speed);
    setAnimationSpeed(speed);
  };

  const handleClose = () => toggleSettings(false);

  if (!isOpen) {
    return null;
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg" isCentered>
      <ModalOverlay bg="blackAlpha.700" backdropFilter="blur(5px)" />
      <ModalContent
        bg="brand.bg"
        color="brand.text"
        borderWidth={1}
        borderColor="brand.primary"
      >
        <ModalHeader fontFamily="heading" color="brand.accent">
          Settings
        </ModalHeader>
        <ModalCloseButton _hover={{ bg: "brand.secondary" }} />
        <ModalBody pb={6}>
          <VStack spacing={6} align="stretch">
            {/* Master Volume */}
            <FormControl>
              <FormLabel htmlFor="master-volume">Master Volume</FormLabel>
              <HStack>
                <Slider
                  id="master-volume"
                  aria-label="master-volume-slider"
                  min={0}
                  max={100}
                  step={1}
                  value={localMasterVolume}
                  onChange={setLocalMasterVolume}
                  onChangeEnd={handleMasterVolumeSliderChangeEnd}
                  colorScheme="yellow"
                  focusThumbOnChange={false}
                >
                  <SliderTrack bg="gray.600">
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb boxSize={5} />
                </Slider>
                <Text w="40px" textAlign="right">
                  {localMasterVolume}%
                </Text>
              </HStack>
            </FormControl>

            {/* Effects Volume */}
            <FormControl>
              <FormLabel htmlFor="effects-volume">
                Sound Effects Volume
              </FormLabel>
              <HStack>
                <Slider
                  id="effects-volume"
                  aria-label="effects-volume-slider"
                  min={0}
                  max={100}
                  step={1}
                  value={localEffectsVolume}
                  onChange={setLocalEffectsVolume}
                  onChangeEnd={handleEffectsVolumeSliderChangeEnd}
                  colorScheme="yellow"
                  focusThumbOnChange={false}
                >
                  <SliderTrack bg="gray.600">
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb boxSize={5} />
                </Slider>
                <Text w="40px" textAlign="right">
                  {localEffectsVolume}%
                </Text>
              </HStack>
            </FormControl>

            {/* Animation Speed */}
            <FormControl>
              <FormLabel htmlFor="animation-speed">
                Text Animation Speed
              </FormLabel>
              <Select
                id="animation-speed"
                value={localAnimationSpeed}
                onChange={handleAnimationSpeedChange}
                bg="gray.700"
                borderColor="gray.600"
                _hover={{ borderColor: "brand.secondary" }}
                focusBorderColor="brand.primary"
              >
                <option value={50}>Fast</option>
                <option value={30}>Medium</option>
                <option value={15}>Slow</option>
                <option value={1000}>Very Fast (Debug)</option>
                <option value={0}>Instant</option>
              </Select>
            </FormControl>

            {/* Theme Toggle */}
            <FormControl display="flex" alignItems="center">
              <FormLabel htmlFor="theme-toggle" mb="0">
                Dark Mode
              </FormLabel>
              <Switch
                id="theme-toggle"
                isChecked={colorMode === "dark"}
                onChange={toggleColorMode}
                colorScheme="yellow"
              />
            </FormControl>
          </VStack>
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
