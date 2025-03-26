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
  Switch,
  useColorMode,
  Select,
} from "@chakra-ui/react";
import { useState } from "react"; // For local state if not using global state immediately

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  // --- Props to connect to global state ---
  // Example:
  masterVolume: number;
  onMasterVolumeChange: (value: number) => void;
  effectsVolume: number;
  onEffectsVolumeChange: (value: number) => void;
  animationSpeed: number; // Representing speed, e.g., 10, 30, 50, 0 (instant)
  onAnimationSpeedChange: (speed: number) => void;
  // --- End Example Props ---
}

export function SettingsModal({
  isOpen,
  onClose,
  // --- Destructure props ---
  masterVolume: initialMasterVolume,
  onMasterVolumeChange,
  effectsVolume: initialEffectsVolume,
  onEffectsVolumeChange,
  animationSpeed: initialAnimationSpeed,
  onAnimationSpeedChange,
}: SettingsModalProps) {
  const { colorMode, toggleColorMode } = useColorMode();

  // Local state for sliders (update global state on change commit or drag end)
  // This provides better performance than updating global state on every tiny slider move
  const [localMasterVolume, setLocalMasterVolume] =
    useState(initialMasterVolume);
  const [localEffectsVolume, setLocalEffectsVolume] =
    useState(initialEffectsVolume);
  const [localAnimationSpeed, setLocalAnimationSpeed] = useState(
    initialAnimationSpeed
  );

  const handleMasterVolumeSliderChangeEnd = (value: number) => {
    onMasterVolumeChange(value); // Update global state
  };
  const handleEffectsVolumeSliderChangeEnd = (value: number) => {
    onEffectsVolumeChange(value); // Update global state
  };
  const handleAnimationSpeedChange = (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const speed = parseInt(event.target.value, 10);
    setLocalAnimationSpeed(speed);
    onAnimationSpeedChange(speed); // Update global state
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay bg="blackAlpha.700" backdropFilter="blur(5px)" />
      <ModalContent
        bg="brand.bgDark"
        color="brand.textLight"
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
                  value={localMasterVolume} // Use local state for controlled input
                  onChange={setLocalMasterVolume} // Update local state during drag
                  onChangeEnd={handleMasterVolumeSliderChangeEnd} // Update global state on release
                  colorScheme="yellow" // Use accent color
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
                <option value="50">Fast</option>
                <option value="30">Medium</option>
                <option value="15">Slow</option>
                <option value="1000">Very Fast (Debug)</option>
                <option value="0">Instant</option>
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
                colorScheme="yellow" // Use accent color
              />
            </FormControl>
          </VStack>
        </ModalBody>

        <ModalFooter borderTopWidth={1} borderColor="brand.primary">
          <Button variant="outline" colorScheme="gray" onClick={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
